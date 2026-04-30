#!/usr/bin/env bash

set -e

JMRI_VERSION="${JMRI_VERSION:-5.14}"

if [[ -n "${SUPERVISOR_TOKEN:-}" && -f /usr/lib/bashio/bashio.sh ]]; then
    # shellcheck source=/dev/null
    source /usr/lib/bashio/bashio.sh
fi

log() {
    if declare -f bashio::log.info &>/dev/null; then
        bashio::log.info "$1"
    else
        echo "[jmri] $1"
    fi
}

PREFS="${JMRI_PREFS_PATH:-/config/jmri}"

# Read settings/profile override from HA add-on config (supervisor only)
if declare -f bashio::config &>/dev/null; then
    JMRI_PROFILE="$(bashio::config 'profile')"
    if [[ -n "${JMRI_PROFILE}" ]]; then
        PREFS="${JMRI_PROFILE}"
        log "Using profile path: ${PREFS}"
    fi
fi

mkdir -p "${PREFS}"
PROFILE_DIR="${PREFS}/profile"

# Seed a default profile on first boot so the JSON/web server starts automatically.
if [[ ! -f "${PROFILE_DIR}/profile.properties" ]]; then
    log "Initializing default JMRI profile..."
    cp -r /opt/jmri/default-profile/. "${PREFS}/"
fi

# Existing installs may have been seeded before the profile format was fixed.
if grep -q '^profile\.id=' "${PROFILE_DIR}/profile.properties" 2>/dev/null; then
    cat > "${PROFILE_DIR}/profile.properties" << 'EOF'
id=jmri-ha-docker
name=HA Docker
EOF
fi

# Remove the broken default LocoNet simulator class from early seeded profiles.
if grep -q 'jmri.jmrix.loconet.sim.configurexml.LocoNetSimulatorConnectionConfigXml' "${PROFILE_DIR}/profile.xml" 2>/dev/null; then
    sed -i '/<connections xmlns=.*connections-2-9-6.xsd">/,/<\/connections>/d' "${PROFILE_DIR}/profile.xml"
    rm -f "${PROFILE_DIR}/preferences/jmri.jmrix.loconet.sim.LocoNetSimulatorAdapter.xml"
fi

# Always write the web server preferences so JMRI starts on port 12090.
# JMRI ignores -D flags when a saved preferences file exists, so we
# write it directly every boot rather than relying on a one-time migration.
mkdir -p "${PREFS}/preferences"
cat > "${PREFS}/preferences/jmri.web.server.WebServerPreferences.xml" << 'WEBPREFS'
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE preferences SYSTEM "http://java.sun.com/dtd/preferences.dtd">
<preferences EXTERNAL_XML_VERSION="1.0">
  <root type="user">
    <map/>
    <node name="jmri">
      <map/>
      <node name="web">
        <map/>
        <node name="server">
          <map>
            <entry key="port" value="12090"/>
            <entry key="startAtStartup" value="true"/>
            <entry key="allowRemoteConfig" value="false"/>
            <entry key="readonlyServer" value="false"/>
          </map>
        </node>
      </map>
    </node>
  </root>
</preferences>
WEBPREFS

# Remove an invalid compatibility file created by early add-on builds. Modern
# JMRI profile XML must stay in profile.xml; ProfileConfig.xml is a legacy format.
if grep -q '<auxiliary-configuration' "${PROFILE_DIR}/ProfileConfig.xml" 2>/dev/null; then
    rm -f "${PROFILE_DIR}/ProfileConfig.xml"
fi

# Always regenerate profiles.xml with the correct absolute path so JMRI
# can locate the profile directory regardless of where PREFS is mounted.
cat > "${PREFS}/profiles.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<profileConfig>
  <profiles>
    <profile id="jmri-ha-docker" path="${PREFS}" autoStart="true" />
  </profiles>
  <searchPaths>
    <searchPath path="${PREFS}" />
  </searchPaths>
</profileConfig>
EOF

log "Starting JMRI ${JMRI_VERSION:-unknown} on internal port 12090, nginx on 12080"
log "Preferences: ${PREFS}"

# Start nginx reverse proxy (rewrites absolute paths for HA ingress compatibility)
nginx -g "daemon off;" &

# Start a virtual framebuffer so PanelPro's GUI components can initialize.
Xvfb :1 -screen 0 1024x768x16 -nolisten tcp &
export DISPLAY=:1
sleep 1

exec /opt/jmri/PanelPro \
    --settingsdir="${PREFS}" \
    --profile="${PREFS}" \
    "-Djmri.web.server.port=12090" \
    "-Djmri.web.server.startAtStartup=true"
