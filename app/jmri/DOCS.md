# JMRI Model Railroad

## What It Does

This app starts JMRI PanelPro in a virtual framebuffer so the JMRI web server can
run inside Home Assistant.

The web interface is available from the app page through Home Assistant ingress.
The JMRI web server also listens on port `12080` if you expose the port.

## Configuration

### `profile`

Optional path to a JMRI profile directory inside the app container.

Leave this blank for the default managed profile. The app stores its managed
profile under the app configuration folder so it survives restarts and upgrades.

## Pairing With The Integration

When using the JMRI Home Assistant integration, configure it with:

- Host: `localhost` when the integration is running in the same Home Assistant
  instance as this app
- Port: `12080`

If Home Assistant cannot reach `localhost`, use the app host address shown by
Home Assistant for the exposed port.
