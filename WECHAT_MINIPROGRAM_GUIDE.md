# 智能部署助手 - 微信小程序转换指南

本文档说明如何将「智能部署助手」单文件 HTML 项目转换为微信小程序，涵盖方案对比、推荐方案、注册流程和上架要求。

---

## 目录

- [一、方案对比](#一方案对比)
- [二、推荐方案：uni-app 重写](#二推荐方案uni-app-重写)
- [三、备选方案：web-view 嵌套](#三备选方案web-view-嵌套)
- [四、微信小程序注册流程](#四微信小程序注册流程)
- [五、微信小程序上架要求](#五微信小程序上架要求)
- [六、费用说明](#六费用说明)
- [七、开发注意事项](#七开发注意事项)

---

## 一、方案对比

将单文件 HTML 项目转换为微信小程序，主要有两种方案：

| 对比项 | web-view 嵌套方案 | uni-app / Taro 重写方案 |
|--------|-------------------|------------------------|
| **开发工作量** | 极少（1-2 天） | 较多（1-2 周） |
| **用户体验** | ⭐⭐ 较差，本质是网页 | ⭐⭐⭐⭐⭐ 优秀，原生体验 |
| **加载速度** | 慢，每次加载网页 | 快，本地渲染 |
| **离线使用** | 不支持 | 部分支持 |
| **微信审核** | ⚠️ 较难通过 | ✅ 容易通过 |
| **功能限制** | 受限，无法调用原生能力 | 可调用微信全部 API |
| **域名要求** | 需要已备案的域名 | 需要已备案的域名 |
| **后续维护** | 简单，改网页即可 | 需要重新编译发布 |
| **个人主体** | 不支持 | 部分类目支持 |

### 方案总结

- **web-view 嵌套**：适合快速验证、临时方案，但审核通过率低，用户体验差
- **框架重写**：工作量大但体验好，审核容易通过，推荐正式使用

---

## 二、推荐方案：uni-app 重写

### 2.1 为什么选择 uni-app

| 优势 | 说明 |
|------|------|
| 一套代码多端运行 | 同时生成微信小程序、H5、App |
| Vue 语法 | 前端开发者上手快 |
| 生态丰富 | 大量 UI 组件库（如 uView） |
| 官方维护 | DCloud 团队持续更新 |

### 2.2 项目结构规划

```
deploy-easy-miniapp/
├── pages/
│   ├── index/           # 首页（服务状态概览）
│   │   ├── index.vue
│   │   └── index.css
│   ├── services/        # 服务管理页
│   │   └── services.vue
│   ├── deploy/          # 部署操作页
│   │   └── deploy.vue
│   ├── logs/            # 日志查看页
│   │   └── logs.vue
│   └── settings/        # 设置页
│       └── settings.vue
├── components/          # 公共组件
│   ├── StatusBar.vue
│   └── ServiceCard.vue
├── api/
│   └── index.js         # API 请求封装
├── static/              # 静态资源
│   └── logo.png
├── App.vue
├── main.js
├── manifest.json        # 小程序配置
├── pages.json           # 页面路由配置
└── uni.scss
```

### 2.3 核心代码示例

**API 请求封装（api/index.js）：**

```javascript
const BASE_URL = 'https://deploy.zhinenti.cn/api';

export const request = (options) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          uni.showToast({ title: '请求失败', icon: 'none' });
          reject(res);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络错误', icon: 'none' });
        reject(err);
      }
    });
  });
};

// 获取服务状态
export const getServices = () => request({ url: '/services' });

// 执行部署
export const deployService = (serviceId) => request({
  url: '/deploy',
  method: 'POST',
  data: { serviceId }
});
```

**页面示例（pages/index/index.vue）：**

```vue
<template>
  <view class="container">
    <view class="header">
      <text class="title">智能部署助手</text>
      <text class="subtitle">服务状态概览</text>
    </view>

    <view class="service-list">
      <view
        v-for="service in services"
        :key="service.id"
        class="service-card"
        :class="{ 'is-running': service.status === 'running' }"
      >
        <text class="service-name">{{ service.name }}</text>
        <text class="service-status">{{ service.statusText }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getServices } from '@/api/index.js';

export default {
  data() {
    return {
      services: []
    };
  },
  onLoad() {
    this.loadServices();
  },
  methods: {
    async loadServices() {
      try {
        const data = await getServices();
        this.services = data.services || [];
      } catch (e) {
        console.error('加载服务列表失败', e);
      }
    }
  }
};
</script>
```

### 2.4 转换步骤

1. **安装 HBuilderX**
   - 下载：https://www.dcloud.io/hbuilderx.html
   - 或使用 Vue CLI：`npm install -g @dcloudio/uni-cli`

2. **创建 uni-app 项目**
   ```bash
   # 使用 Vue CLI 创建
   npx degit dcloudio/uni-preset-vue#vite deploy-easy-miniapp
   cd deploy-easy-miniapp
   npm install
   ```

3. **迁移页面逻辑**
   - 将原 HTML 中的各功能模块拆分为独立页面
   - 将 `fetch` API 调用替换为 `uni.request`
   - 将 DOM 操作替换为 Vue 响应式数据

4. **适配样式**
   - 将 `rem/em` 单位改为 `rpx`（小程序推荐单位）
   - 去除不兼容的 CSS 属性
   - 使用 `wx:if` / `v-if` 替代 JS 显示隐藏逻辑

5. **编译为微信小程序**
   ```bash
   # 编译
   npm run dev:mp-weixin
   # 输出目录: dist/dev/mp-weixin
   ```

6. **导入微信开发者工具**
   - 下载微信开发者工具：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
   - 导入 `dist/dev/mp-weixin` 目录
   - 预览和调试

---

## 三、备选方案：web-view 嵌套

如果时间紧迫或功能简单，可以使用 web-view 直接嵌套现有网页。

### 3.1 前提条件

- 域名已完成 ICP 备案
- 域名已在小程序后台配置为「业务域名」
- 网页已配置好响应式适配

### 3.2 代码示例

**pages/index/index.wxml：**
```xml
<web-view src="https://deploy.zhinenti.cn"></web-view>
```

**pages.json：**
```json
{
  "pages": [
    {
      "path": "pages/index/index",
      "style": {
        "navigationBarTitleText": "智能部署助手"
      }
    }
  ]
}
```

### 3.3 业务域名配置

1. 登录微信公众平台 → 「开发」→「开发管理」→「开发设置」
2. 找到「业务域名」→ 点击「添加」
3. 输入 `deploy.zhinenti.cn`
4. 下载校验文件，放置到网站根目录
5. 点击「确认」完成验证

### 3.4 局限性

- ⚠️ 个人主体小程序不支持 web-view
- ⚠️ web-view 中的页面无法调用微信原生 API（如扫码、支付）
- ⚠️ 每个小程序最多配置 20 个业务域名
- ⚠️ 审核时可能因「功能过于简单」被拒

---

## 四、微信小程序注册流程

### 4.1 注册步骤

1. 访问微信公众平台：https://mp.weixin.qq.com/
2. 点击右上角「立即注册」
3. 选择「小程序」
4. 填写未注册过公众号/小程序的邮箱
5. 邮箱验证 → 选择主体类型：
   - **个人**：免费，但功能受限（不支持 web-view、不支持支付）
   - **企业/个体工商户**：需营业执照，功能完整
6. 填写主体信息 → 完成注册

### 4.2 主体类型对比

| 能力 | 个人主体 | 企业主体 |
|------|----------|----------|
| 注册费用 | 免费 | 认证 300 元/年 |
| web-view | ❌ 不支持 | ✅ 支持 |
| 微信支付 | ❌ 不支持 | ✅ 支持 |
| 获取手机号 | ❌ 不支持 | ✅ 支持 |
| 类目限制 | 较少 | 完整 |
| 审核宽松度 | 较严 | 相对宽松 |

> 💡 **建议**：如果是企业应用，强烈建议使用企业主体验证。

---

## 五、微信小程序上架要求

### 5.1 基本要求

| 项目 | 要求 |
|------|------|
| 小程序名称 | 4-30 个字符，不得侵权 |
| 小程序头像 | 144×144 以上，清晰可辨 |
| 小程序简介 | 4-120 个字符 |
| 服务类目 | 需与实际功能匹配 |
| 隐私政策 | 必须提供 |
| 域名备案 | 所有请求域名必须已备案 |
| HTTPS | 所有请求必须使用 HTTPS |

### 5.2 内容要求

- 不得包含违法违规内容
- 不得诱导分享、诱导关注
- 不得过度营销
- 功能需完整可用，不得只是「壳」

### 5.3 技术合规

- 首次启动需展示隐私协议弹窗
- 收集用户信息需明确告知并获取同意
- 不得在用户不知情时收集数据
- 小程序包体积限制：主包 ≤ 2MB，总计 ≤ 20MB

### 5.4 发布流程

1. 在微信开发者工具中点击「上传」
2. 登录微信公众平台 → 「管理」→「版本管理」
3. 在「开发版本」中找到刚上传的版本
4. 点击「提交审核」
5. 填写审核信息（功能页面、测试账号等）
6. 等待审核（通常 1-3 个工作日）
7. 审核通过后点击「发布」

---

## 六、费用说明

| 项目 | 费用 | 备注 |
|------|------|------|
| **小程序注册（个人）** | 免费 | 功能受限 |
| **微信认证（企业）** | ¥300/年 | 必须认证才能使用完整功能 |
| **域名备案** | 免费 | 需自行到通信管理局备案 |
| **SSL 证书** | 免费/付费 | Let's Encrypt 免费 |
| **uni-app 开发** | 免费 | 开源框架 |
| **HBuilderX** | 免费 | DCloud 官方 IDE |

### 费用汇总

- **个人开发者（功能受限）**：**¥0/年**
- **企业开发者（推荐）**：**¥300/年**

---

## 七、开发注意事项

### 7.1 小程序 vs Web 的差异

| Web | 小程序 |
|-----|--------|
| `document.xxx` | ❌ 不支持，使用 Vue 数据驱动 |
| `window.xxx` | ⚠️ 部分支持 |
| `fetch / XMLHttpRequest` | ✅ 用 `uni.request` 替代 |
| `localStorage` | ✅ 用 `uni.setStorage` 替代 |
| `rem / em` | ✅ 推荐用 `rpx` |
| 外部字体 / CDN 资源 | ⚠️ 需配置白名单 |
| `eval` / `new Function` | ❌ 不支持 |

### 7.2 性能优化建议

1. **分包加载**：将不常用页面放入子包，减少主包大小
2. **图片优化**：使用 CDN 图片，避免打包大图
3. **数据缓存**：使用 `uni.setStorage` 缓存常用数据
4. **骨架屏**：提升首屏加载体验
5. **预加载**：利用 `onReachBottom` 预加载下一页数据

### 7.3 推荐技术栈

```
uni-app (Vue 3 + Vite)
├── UI 框架: uView Plus / uni-ui
├── 状态管理: Pinia
├── 请求封装: luch-request
└── 工具库: dayjs
```

---

> 📝 本文档基于微信小程序基础库 2.x、uni-app Vue3 版本编写，最后更新：2025 年
