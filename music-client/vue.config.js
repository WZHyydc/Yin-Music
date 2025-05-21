const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  chainWebpack: config => {
    config.plugin('define').tap(definitions => {
      Object.assign(definitions[0]['process.env'], {
        // 在远程部署or容器部署时，应打开此开关，地址内容为服务器地址
        NODE_HOST: '"http://172.24.161.22:8888"',
        // 在本地部署时，应打开此开关
        // Node_HOST: '"http://127.0.0.1:8888"',
      });
      return definitions;
    });
  }
})
