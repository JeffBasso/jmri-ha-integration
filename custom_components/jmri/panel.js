class JMRIPanel extends HTMLElement {
  connectedCallback() {
    this.render();
  }

  set panel(panel) {
    this._panel = panel;
    this.render();
  }

  render() {
    const url = this._panel?.config?.url || "/api/jmri_proxy/";

    this.innerHTML = `
      <style>
        :host {
          display: block;
          height: 100%;
        }

        iframe {
          border: 0;
          display: block;
          height: 100%;
          width: 100%;
        }
      </style>
      <iframe title="JMRI" src="${url}"></iframe>
    `;
  }
}

customElements.define("jmri-panel", JMRIPanel);
