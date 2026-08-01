const config = {
  appId: 'com.zhinenti.deploy',
  appName: '智能部署助手',
  webDir: 'frontend',
  server: {
    url: 'https://deploy.zhinenti.cn',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: '#0d1117',
      showSpinner: false,
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0d1117',
    },
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },
  },
  android: {
    allowMixedContent: true,
    captureInput: true,
    webContentsDebuggingEnabled: false,
  },
};
module.exports = config;
