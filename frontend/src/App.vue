<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left" @click="logoClickCount++">
        <span class="logo">🚀</span>
        <h1>智能部署助手</h1>
        <span class="version">v3.0</span>
      </div>
      <div class="header-right">
        <div class="tab-bar">
          <button class="tab-btn" :class="{ active: activeTab === 'deploy' }" @click="activeTab = 'deploy'">
             免费部署
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'generate' }" @click="activeTab = 'generate'">
            ✨ 生成项目
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'fix' }" @click="activeTab = 'fix'">
            🔧 代码检测
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'editcode' }" @click="activeTab = 'editcode'">
            🛠 代码修改
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'projects' }" @click="activeTab = 'projects'">
            📦 项目中心
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'skills' }" @click="activeTab = 'skills'">
            ⚙️ 配置生成
          </button>
          <button v-if="isAdmin" class="tab-btn admin-tab" :class="{ active: activeTab === 'admin' }" @click="activeTab = 'admin'">
            🛡️ 管理后台
          </button>
        </div>
        <div class="header-actions">
          <template v-if="isLoggedIn">
            <el-popover placement="bottom-end" :width="320" trigger="click" @show="loadUserProfile">
              <template #reference>
                <div class="user-tag-wrapper">
                  <el-tag type="info" effect="plain" round size="small" class="user-tag-clickable">
                    👤 {{ loggedInUsername }}
                  </el-tag>
                  <el-tag v-if="userCredits > 0" type="warning" effect="plain" round size="small" class="credits-badge-small">
                    💎 {{ formatCredits(userCredits) }}
                  </el-tag>
                </div>
              </template>
              <div class="profile-popover">
                <div class="profile-header">
                  <div class="profile-avatar">{{ loggedInUsername ? loggedInUsername[0].toUpperCase() : '?' }}</div>
                  <div class="profile-name">{{ userProfile.username || loggedInUsername }}</div>
                </div>
                <div class="profile-info">
                  <div class="profile-row">
                    <span class="profile-label">积分余额</span>
                    <span class="profile-value" style="color: var(--accent-orange); font-weight: 700;">💎 {{ formatCredits(userCredits) }}</span>
                  </div>
                  <div class="profile-row">
                    <span class="profile-label">账户状态</span>
                    <el-tag :type="userCredits > 0 ? 'success' : 'info'" size="small" effect="dark">{{ userCredits > 0 ? '有积分' : '无积分' }}</el-tag>
                  </div>
                  <div class="profile-row">
                    <span class="profile-label">注册时间</span>
                    <span class="profile-value">{{ formatFullTime(userProfile.created_at) }}</span>
                  </div>
                  <div class="profile-row">
                    <span class="profile-label">用户ID</span>
                    <span class="profile-value mono">{{ userId }}</span>
                  </div>
                </div>
                <div class="profile-actions">
                  <el-button type="primary" size="small" @click="showPaymentDialog" style="width: 100%;">💎 充值积分</el-button>
                  <el-button type="danger" size="small" plain @click="handleLogout" style="width: 100%;">退出登录</el-button>
                </div>
              </div>
            </el-popover>
          </template>
          <el-button v-else text size="small" type="primary" @click="loginMode = 'login'; loginDialogVisible = true">登录</el-button>
          <el-tag v-show="false" type="warning" effect="plain" round class="vip-tag" @click="showPaymentDialog">
            💎 充值积分
          </el-tag>
          <button v-if="showInstallBtn" @click="installPWA" class="pwa-install-btn">
            添加到桌面
          </button>
        </div>
      </div>
    </header>

    <!-- ============ 部署 Tab ============ -->
    <main v-if="activeTab === 'deploy'" class="main-content">
      <!-- 使用说明 -->
      <section class="step-section usage-guide">
        <div class="guide-header" @click="guideExpanded = !guideExpanded">
          <span class="guide-icon">📖</span>
          <span class="guide-title">使用说明</span>
          <el-icon class="guide-arrow" :class="{ expanded: guideExpanded }"><ArrowDown /></el-icon>
        </div>
        <div v-show="guideExpanded" class="guide-body">
          <div class="guide-steps">
            <div class="guide-step">
              <span class="guide-step-num">1</span>
              <div class="guide-step-content">
                <h4>输入项目路径</h4>
                <p>填写服务器上项目的绝对路径，或从下拉列表选择已有项目，点击「检测」按钮识别项目类型</p>
              </div>
            </div>
            <div class="guide-step">
              <span class="guide-step-num">2</span>
              <div class="guide-step-content">
                <h4>确认项目信息</h4>
                <p>系统自动识别项目类型（Python/Node.js/Go/PHP/Java 等）、框架和包管理器</p>
              </div>
            </div>
            <div class="guide-step">
              <span class="guide-step-num">3</span>
              <div class="guide-step-content">
                <h4>选择部署方式</h4>
                <p>支持部署到服务器、Docker 容器、Cloudflare Pages 等多种方式</p>
              </div>
            </div>
            <div class="guide-step">
              <span class="guide-step-num">4</span>
              <div class="guide-step-content">
                <h4>生成并执行</h4>
                <p>一键生成部署脚本，支持复制、下载或直接远程部署到目标服务器</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 1: 选择检测方式 -->
      <section class="step-section">
        <div class="step-header">
          <span class="step-num">1</span>
          <span class="step-title">选择检测方式</span>
        </div>
        <div class="step-body">
          <div class="fix-mode-tabs">
            <div class="fix-mode-card" :class="{ active: deployMode === 'upload' }" @click="deployMode = 'upload'; onDeployModeChange()">
              <div class="fix-mode-icon">📤</div>
              <div class="fix-mode-label">上传项目</div>
              <div class="fix-mode-desc">上传ZIP自动识别并推荐部署方案</div>
            </div>
            <div class="fix-mode-card" :class="{ active: deployMode === 'server' }" @click="deployMode = 'server'; onDeployModeChange()">
              <div class="fix-mode-icon">🖥️</div>
              <div class="fix-mode-label">连接服务器</div>
              <div class="fix-mode-desc">选择服务器，输入项目路径检测</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 上传模式内容 -->
      <section v-if="deployMode === 'upload'" class="step-section">
        <div class="step-body">
          <div class="upload-zone" @click="triggerDeployZipSelect" @dragover.prevent @drop.prevent="handleDeployZipDrop">
            <div class="upload-icon">📦</div>
            <div class="upload-text">拖拽 ZIP 文件到此处，或 <em>点击选择</em></div>
            <div class="upload-hint">支持 .zip 格式，最大 20MB</div>
          </div>
          <input ref="deployZipInput" type="file" accept=".zip" style="display:none" @change="handleDeployZipSelect" />
          <div v-if="deployUploadFile" class="file-info-bar">
            📎 {{ deployUploadFile.name }} ({{ formatFileSize(deployUploadFile.size) }})
            <el-button text size="small" @click="deployUploadFile = null" style="margin-left: 8px; color: var(--text-secondary);">✕</el-button>
          </div>
          <el-button type="primary" size="large" :loading="detecting" :disabled="!deployUploadFile" @click="detectUploadedProject" style="margin-top:12px">
            🔍 检测项目
          </el-button>
        </div>
      </section>

      <!-- 服务器模式：路径选择（仅连接后显示） -->
      <section v-if="deployMode === 'server' && sshConnected" class="step-section">
        <div class="step-header">
          <span class="step-num">2</span>
          <span class="step-title">项目路径</span>
        </div>
        <div class="step-body">
          <div class="path-section">
            <div class="path-select-row">
              <span class="path-select-label">远程项目：</span>
              <el-select v-model="projectPath" placeholder="选择远程项目目录" filterable clearable size="large" style="flex:1" @change="onPathSelect" :loading="scanningPaths">
                <el-option v-for="p in availablePaths" :key="p.path" :label="p.path" :value="p.path">
                  <span>📁 {{ p.name }}</span>
                  <span style="color: var(--text-secondary); font-size: 12px; margin-left: 8px;">{{ p.path }}</span>
                </el-option>
              </el-select>
              <el-button size="large" @click="scanRemotePaths" :loading="scanningPaths">
                刷新
              </el-button>
            </div>
            <el-input v-model="projectPath" placeholder="或输入远程项目路径 /www/wwwroot/..." size="large" clearable @keyup.enter="detectProject">
              <template #prefix><el-icon><Folder /></el-icon></template>
              <template #append>
                <el-button type="primary" :loading="detecting" @click="detectProject" :disabled="!sshConnected">
                  <el-icon v-if="!detecting"><Search /></el-icon>
                  检测
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
      </section>

      <!-- Step 2 -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">2</span>
          <span class="step-title">项目信息</span>
        </div>
        <div class="step-body">
          <div class="info-grid">
            <div class="info-item"><span class="info-label">📦 项目名称</span><span class="info-value highlight">{{ projectInfo.project_name }}</span></div>
            <div class="info-item"><span class="info-label">🏗️ 项目类型</span><el-tag :type="typeTagColor(projectInfo.type)" effect="dark">{{ projectInfo.type }}</el-tag></div>
            <div class="info-item"><span class="info-label">🔧 框架</span><el-tag v-if="projectInfo.framework" type="info" effect="plain">{{ projectInfo.framework }}</el-tag><span v-else class="info-value dim">-</span></div>
            <div class="info-item"><span class="info-label">📋 包管理器</span><el-tag v-if="projectInfo.package_manager" type="warning" effect="plain">{{ projectInfo.package_manager }}</el-tag><span v-else class="info-value dim">-</span></div>
            <div class="info-item"><span class="info-label">🐳 Docker</span><el-tag :type="projectInfo.has_docker ? 'success' : 'info'" effect="plain">{{ projectInfo.has_docker ? '已配置' : '未配置' }}</el-tag></div>
            <div class="info-item" v-if="projectInfo.entry_point"><span class="info-label">🔗 入口</span><span class="info-value code">{{ projectInfo.entry_point }}</span></div>
          </div>
        </div>
      </section>

      <!-- Step 3 -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">3</span>
          <span class="step-title">部署配置</span>
        </div>
        <div class="step-body">
          <div class="config-row">
            <div class="config-item">
              <label>部署方式</label>
              <el-select v-model="deployType" placeholder="选择部署方式" size="large" style="width:100%">
                <el-option v-for="opt in deployOptions" :key="opt.value" :label="opt.label" :value="opt.value">
                  <span>{{ opt.icon }} {{ opt.label }}</span>
                </el-option>
              </el-select>
            </div>
            <div class="config-item" v-if="deployType === 'server' && servers.length > 0">
              <label>目标服务器</label>
              <el-select v-model="selectedServerIdx" placeholder="选择服务器" size="large" style="width:100%">
                <el-option v-for="(s, i) in servers" :key="i" :label="`${s.name} (${s.host})`" :value="i" />
              </el-select>
            </div>
            <div class="config-item" v-if="deployType === 'server'">
              <label>域名/IP</label>
              <el-input v-model="domain" placeholder="example.com 或 IP" size="large" />
            </div>
          </div>
        </div>
      </section>

      <!-- Step 4 -->
      <section v-if="projectInfo" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">4</span>
          <span class="step-title">生成部署脚本</span>
        </div>
        <div class="step-body">
          <div class="action-row">
            <el-button type="primary" size="large" :loading="generating" @click="generateScript">
              <el-icon v-if="!generating"><VideoPlay /></el-icon>
              生成脚本
            </el-button>
            <el-button v-if="scriptOutput && deployType === 'server'" type="success" size="large" :disabled="remoteDeploying" @click="startRemoteDeploy">
              <el-icon v-if="!remoteDeploying"><Upload /></el-icon>
              {{ remoteDeploying ? '部署中...' : '🚀 远程部署' }}
            </el-button>
            <span class="free-badge">🆓 部署功能永久免费</span>
          </div>

          <!-- Terminal Output -->
          <div v-if="scriptOutput" class="terminal-container fade-in">
            <div class="terminal-header">
              <div class="terminal-dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
              <span class="terminal-title">{{ scriptFilename }}</span>
              <div class="terminal-actions">
                <el-button text size="small" @click="copyScript"><el-icon><CopyDocument /></el-icon>{{ copied ? '已复制!' : '复制' }}</el-button>
                <el-button text size="small" @click="downloadScript"><el-icon><Download /></el-icon>下载</el-button>
              </div>
            </div>
            <div class="terminal-body"><pre><code>{{ scriptOutput }}</code></pre></div>
          </div>

          <!-- Remote Deploy Log -->
          <div v-if="remoteLogs.length > 0" class="terminal-container fade-in remote-log">
            <div class="terminal-header">
              <div class="terminal-dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
              <span class="terminal-title">🚀 远程部署日志</span>
              <div class="terminal-actions">
                <el-tag v-if="remoteStatus === 'success'" type="success" size="small">部署成功</el-tag>
                <el-tag v-else-if="remoteStatus === 'failed' || remoteStatus === 'error'" type="danger" size="small">部署失败</el-tag>
                <el-tag v-else type="warning" size="small" class="pulse-tag">部署中...</el-tag>
              </div>
            </div>
            <div class="terminal-body" ref="remoteLogBody">
              <pre><code v-for="(log, i) in remoteLogs" :key="i" :class="{'log-warn': log.startsWith('⚠️'), 'log-err': log.startsWith('❌'), 'log-ok': log.startsWith('✅') || log.startsWith('🎉')}">{{ log }}</code></pre>
            </div>
          </div>

          <!-- Extra files -->
          <div v-if="extraFiles.length > 0" class="extra-files fade-in">
            <h4>📎 附加文件</h4>
            <div v-for="file in extraFiles" :key="file.filename" class="extra-file-item">
              <div class="extra-file-header">
                <span>{{ file.filename }}</span>
                <el-button text size="small" @click="copyExtra(file.content)"><el-icon><CopyDocument /></el-icon></el-button>
                <el-button text size="small" @click="downloadExtra(file)"><el-icon><Download /></el-icon></el-button>
              </div>
              <div class="terminal-body compact"><pre><code>{{ file.content }}</code></pre></div>
            </div>
          </div>
        </div>
      </section>

      <!-- 底部SSH连接（仅远程模式，默认折叠） -->
      <section v-if="deployMode === 'server'" class="step-section ssh-collapsible">
        <div class="ssh-collapse-header" @click="deploySshCollapsed = !deploySshCollapsed">
          <span>🔗 SSH 连接</span>
          <span v-if="sshConnected" class="ssh-status-connected">🟢 {{ sshForm.host }}</span>
          <el-icon class="guide-arrow" :class="{ expanded: !deploySshCollapsed }"><ArrowDown /></el-icon>
        </div>
        <div v-show="!deploySshCollapsed" class="ssh-collapse-body">
          <!-- Connection Form -->
          <div v-if="!sshConnected" class="ssh-form">
            <div class="ssh-form-row">
              <div class="ssh-form-item" style="flex:2">
                <label>IP / 域名</label>
                <el-input v-model="sshForm.host" placeholder="192.168.1.100 或 example.com" size="large" />
              </div>
              <div class="ssh-form-item" style="flex:1; max-width:140px">
                <label>SSH 端口</label>
                <el-input v-model.number="sshForm.port" placeholder="22" size="large" />
              </div>
            </div>
            <div class="ssh-form-row">
              <div class="ssh-form-item" style="flex:1">
                <label>用户名</label>
                <el-input v-model="sshForm.username" placeholder="root" size="large" />
              </div>
              <div class="ssh-form-item" style="flex:1">
                <label>密码</label>
                <el-input v-model="sshForm.password" type="password" show-password placeholder="服务器密码" size="large" @keyup.enter="connectServer" />
              </div>
            </div>
            <el-button type="primary" size="large" :loading="sshConnecting" @click="connectServer" :disabled="!sshForm.host || !sshForm.password">
              连接服务器
            </el-button>
          </div>
          <!-- Connected State -->
          <div v-else class="ssh-connected">
            <div class="ssh-connected-info">
              <span class="ssh-connected-icon">🖥️</span>
              <div>
                <div class="ssh-connected-host">{{ sshForm.host }}:{{ sshForm.port }}</div>
                <div class="ssh-connected-user">{{ sshForm.username }}@{{ sshForm.host }}</div>
              </div>
            </div>
            <el-button type="danger" size="small" plain @click="disconnectServer">
              断开连接
            </el-button>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 生成项目 Tab ============ -->
    <main v-if="activeTab === 'generate'" class="main-content">
      <section class="step-section">
        <div class="step-header">
          <span class="step-num gen-num">1</span>
          <span class="step-title">描述你的项目</span>
        </div>
        <div class="step-body">
          <el-input v-model="genDescription" type="textarea" :rows="3" placeholder="描述你想要的项目，例如：一个带用户登录和任务管理的 Todo List 应用" size="large" />
          <div class="config-row" style="margin-top: 16px;">
            <div class="config-item">
              <label>项目类型</label>
              <el-select v-model="genProjectType" placeholder="选择类型" size="large" style="width:100%" @change="onGenTypeOnChange">
                <el-option value="frontend" label="🖥️ 前端项目" />
                <el-option value="backend" label="⚙️ 后端项目" />
                <el-option value="fullstack" label="🔗 全栈项目" />
              </el-select>
            </div>
            <div class="config-item">
              <label>技术栈</label>
              <el-select v-model="genTechStack" placeholder="选择技术栈" size="large" style="width:100%">
                <el-option v-for="(info, key) in currentStacks" :key="key" :value="key" :label="info.label">
                  <span>{{ info.label }}</span>
                  <span style="color: #8b949e; font-size: 12px; margin-left: 8px;">{{ info.desc }}</span>
                </el-option>
              </el-select>
            </div>
          </div>
        </div>
      </section>

      <section class="step-section fade-in">
        <div class="step-header">
          <span class="step-num gen-num">2</span>
          <span class="step-title">AI 生成代码</span>
        </div>
        <div class="step-body">
          <el-button type="primary" size="large" :loading="genLoading" @click="generateProject" :disabled="!genDescription.trim()">
            <el-icon v-if="!genLoading"><MagicStick /></el-icon>
            AI 生成项目
          </el-button>
          <span v-if="userCredits < 500" class="pay-hint" @click="showPaymentDialog">
            <el-icon><Lock /></el-icon> 积分不足，充值后使用
          </span>

        </div>
      </section>

      <section v-if="genFiles.length > 0" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num gen-num">3</span>
          <span class="step-title">生成结果</span>
          <span class="selected-count">共 {{ genFiles.length }} 个文件</span>
        </div>
        <div class="step-body">
          <div class="gen-file-list">
            <div v-for="(file, idx) in genFiles" :key="idx" class="gen-file-item" :class="{ active: genSelectedFile === idx }" @click="genSelectedFile = idx">
              <span class="gen-file-icon">📄</span>
              <span class="gen-file-name">{{ file.filename }}</span>
            </div>
          </div>
          <div v-if="genSelectedFile >= 0 && genFiles[genSelectedFile]" class="terminal-container">
            <div class="terminal-header">
              <div class="terminal-dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
              <span class="terminal-title">{{ genFiles[genSelectedFile].filename }}</span>
              <div class="terminal-actions">
                <el-button text size="small" @click="copyGenFile"><el-icon><CopyDocument /></el-icon>复制</el-button>
              </div>
            </div>
            <div class="terminal-body"><pre><code>{{ genFiles[genSelectedFile].content }}</code></pre></div>
          </div>
          <div class="gen-actions" v-if="genFiles.length > 0">
            <el-button type="success" size="large" @click="downloadGenProject">
              <el-icon><Download /></el-icon>
              📥 下载 ZIP
            </el-button>
            <el-button type="primary" size="large" @click="openSaveToServer">
              🖥️ 保存到服务器
            </el-button>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 代码检测 Tab ============ -->
    <main v-if="activeTab === 'fix'" class="main-content">
      <!-- Step 1: 选择检测方式 -->
      <section class="step-section">
        <div class="step-header">
          <span class="step-num fix-num">1</span>
          <span class="step-title">选择检测方式</span>
        </div>
        <div class="step-body">
          <div class="fix-mode-tabs">
            <div class="fix-mode-card" :class="{ active: fixMode === 'remote' }" @click="fixMode = 'remote'">
              <div class="fix-mode-icon">🖥️</div>
              <div class="fix-mode-label">连接服务器</div>
              <div class="fix-mode-desc">选择服务器，输入项目路径</div>
            </div>
            <div class="fix-mode-card" :class="{ active: fixMode === 'upload' }" @click="fixMode = 'upload'">
              <div class="fix-mode-icon">📦</div>
              <div class="fix-mode-label">上传项目</div>
              <div class="fix-mode-desc">上传ZIP文件进行检测</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Step 2A: 连接服务器模式 -->
      <template v-if="fixMode === 'remote'">
        <section class="step-section">
          <div class="step-header">
            <span class="step-num fix-num">2</span>
            <span class="step-title">选择服务器</span>
          </div>
          <div class="step-body">
            <div v-if="servers.length === 0" style="text-align:center; padding: 20px 0;">
              <p style="color: var(--text-secondary); margin-bottom: 8px;">暂无已配置的服务器</p>
              <p style="color: var(--accent-orange); font-size: 13px;">请先去「免费部署」tab 配置服务器信息</p>
            </div>
            <template v-else>
              <el-select v-model="fixServerId" placeholder="选择已配置的服务器" size="large" style="width:100%">
                <el-option v-for="(s, i) in servers" :key="i" :value="String(i)" :label="`${s.name} (${s.host})`" />
              </el-select>
              <el-input v-model="fixProjectPath" placeholder="项目路径，如 /www/wwwroot/my-project" size="large" style="margin-top:12px" clearable @keyup.enter="analyzeRemoteCode" />
              <el-button type="warning" size="large" :loading="analyzing" @click="analyzeRemoteCode" style="margin-top:12px" :disabled="!fixServerId || !fixProjectPath.trim()">
                🔍 开始检测
              </el-button>
            </template>
          </div>
        </section>
      </template>

      <!-- Step 2B: 上传项目模式 -->
      <template v-if="fixMode === 'upload'">
        <section class="step-section">
          <div class="step-header">
            <span class="step-num fix-num">2</span>
            <span class="step-title">上传项目</span>
          </div>
          <div class="step-body">
            <div class="upload-zone" @click="triggerFixZipSelect" @dragover.prevent @drop.prevent="handleFixZipDrop">
              <div class="upload-icon">📦</div>
              <div class="upload-text">拖拽 ZIP 文件到此处，或 <em>点击选择</em></div>
              <div class="upload-hint">支持 .zip 格式，最大 10MB</div>
            </div>
            <input ref="fixZipInput" type="file" accept=".zip" style="display:none" @change="handleFixZipSelect" />
            <div v-if="fixUploadFile" class="file-info-bar">
              📎 {{ fixUploadFile.name }} ({{ formatFileSize(fixUploadFile.size) }})
              <el-button text size="small" @click="fixUploadFile = null" style="margin-left: 8px; color: var(--text-secondary);">✕</el-button>
            </div>
            <el-button type="warning" size="large" :loading="analyzing" :disabled="!fixUploadFile" @click="analyzeUploadedCode" style="margin-top:12px">
              🔍 开始检测
            </el-button>
          </div>
        </section>
      </template>

      <!-- 检测结果展示（两种模式共用） -->
      <section v-if="analysisResult" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num fix-num">{{ fixMode === 'remote' ? '3' : '3' }}</span>
          <span class="step-title">检测结果</span>
          <div class="result-summary" v-if="analysisResult.total > 0">
            <el-tag type="danger" effect="dark" size="small">{{ analysisResult.error_count }} 个错误</el-tag>
            <el-tag type="warning" effect="dark" size="small">{{ analysisResult.warning_count }} 个警告</el-tag>
          </div>
          <div class="result-summary" v-else>
            <el-tag type="success" effect="dark" size="small">✓ 未发现问题</el-tag>
          </div>
        </div>
        <div class="step-body">
          <div v-if="analysisResult.total === 0" class="no-errors">
            <span class="no-errors-icon">🎉</span>
            <p>恭喜！未检测到代码错误</p>
          </div>
          <div v-else class="error-list">
            <div v-for="(err, idx) in analysisResult.errors" :key="idx" class="error-item" :class="[err.severity, { selected: selectedErrors.includes(idx) }]" @click="toggleError(idx)">
              <div class="error-left">
                <span class="error-severity" :class="err.severity">{{ err.severity === 'error' ? '✕' : '⚠' }}</span>
                <span class="error-type-badge">{{ errorTypeLabel(err.error_type) }}</span>
              </div>
              <div class="error-center">
                <span class="error-file">{{ err.file }}</span>
                <span class="error-line" v-if="err.line > 0">:{{ err.line }}</span>
                <p class="error-msg">{{ err.error }}</p>
              </div>
              <div class="error-right">
                <el-checkbox :model-value="selectedErrors.includes(idx)" @click.stop="toggleError(idx)" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 修复区域（两种模式共用） -->
      <section v-if="selectedErrors.length > 0" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num fix-num">4</span>
          <span class="step-title">自动修复</span>
          <span class="selected-count">已选 {{ selectedErrors.length }} 项</span>
        </div>
        <div class="step-body">
          <div class="fix-actions">
            <el-button type="warning" size="large" :loading="repairing" @click="repairErrorsNew">
              <el-icon v-if="!repairing"><Magic /></el-icon>
              AI 自动修复
            </el-button>
            <span v-if="userCredits < 200" class="pay-hint" @click="showPaymentDialog">
              <el-icon><Lock /></el-icon> 积分不足，充值后使用
            </span>
            <el-button size="large" @click="selectAllErrors">全选</el-button>
            <el-button size="large" @click="selectedErrors = []">清空</el-button>
          </div>
          <div v-if="repairResults.length > 0" class="repair-results fade-in">
            <h4>📝 修复对比</h4>
            <div v-for="(result, ridx) in repairResults" :key="ridx" class="repair-item">
              <div class="repair-file-header">
                <span class="repair-filename">{{ result.file }}</span>
                <div style="display:flex;gap:8px;">
                  <el-button v-if="fixMode === 'remote'" type="success" size="small" :disabled="result.applied" @click="applyFix(result)">
                    {{ result.applied ? '✓ 已应用' : '应用修复' }}
                  </el-button>
                </div>
              </div>
              <div class="diff-container">
                <div class="diff-side">
                  <div class="diff-label">原始代码</div>
                  <pre class="diff-code original"><code>{{ result.original }}</code></pre>
                </div>
                <div class="diff-divider"></div>
                <div class="diff-side">
                  <div class="diff-label">修复后</div>
                  <pre class="diff-code fixed"><code>{{ result.fixed }}</code></pre>
                </div>
              </div>
            </div>
            <!-- 上传模式下可下载修复后的ZIP -->
            <div v-if="fixMode === 'upload' && repairResults.length > 0" style="margin-top:16px; text-align:center;">
              <el-button type="success" size="large" @click="downloadRepairedZip">
                📥 下载修复后的 ZIP
              </el-button>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 代码修改 Tab ============ -->
    <main v-if="activeTab === 'editcode'" class="main-content">
      <!-- Step 1: Upload project ZIP -->
      <section class="step-section">
        <div class="step-header">
          <span class="step-num edit-num">1</span>
          <span class="step-title">上传项目源码</span>
        </div>
        <div class="step-body">
          <div class="upload-zone" @click="triggerZipSelect" @dragover.prevent @drop.prevent="handleZipDrop">
            <div class="upload-icon">📦</div>
            <div class="upload-text">拖拽 ZIP 文件到此处，或 <em>点击选择</em></div>
            <div class="upload-hint">支持 .zip 格式，最大 5MB</div>
          </div>
          <input ref="zipInput" type="file" accept=".zip" style="display:none" @change="handleZipSelect" />
          <div v-if="editZipFile" class="file-info-bar">
            📎 {{ editZipFile.name }} ({{ formatFileSize(editZipFile.size) }})
            <el-button text size="small" @click="editZipFile = null" style="margin-left: 8px; color: var(--text-secondary);">✕</el-button>
          </div>
        </div>
      </section>

      <!-- Step 2: Describe modification -->
      <section class="step-section">
        <div class="step-header">
          <span class="step-num edit-num">2</span>
          <span class="step-title">描述修改需求</span>
        </div>
        <div class="step-body">
          <el-input v-model="editCodeDescription" type="textarea" :rows="3" placeholder="描述你想要修改的内容，例如：给项目添加登录功能、优化页面性能、修复XX页面的bug、把前端改成响应式布局..." size="large" />
        </div>
      </section>

      <!-- Step 3: AI modify -->
      <section class="step-section">
        <div class="step-header">
          <span class="step-num edit-num">3</span>
          <span class="step-title">AI 修改项目</span>
        </div>
        <div class="step-body">
          <div class="editcode-actions">
            <el-button type="primary" size="large" :loading="editCodeLoading" @click="aiModifyProject" :disabled="!editZipFile || !editCodeDescription.trim()">
              🤖 AI 修改项目
            </el-button>
            <span v-if="userCredits < 300" class="pay-hint" @click="showPaymentDialog">
              <el-icon><Lock /></el-icon> 积分不足，充值后使用
            </span>
            <el-button v-if="editModifyResult.length > 0" size="large" @click="editModifyResult = []; editCodeSelectedFile = -1; editZipFile = null; editCodeDescription = ''">
              ✕ 清空
            </el-button>
          </div>
        </div>
      </section>

      <!-- Results -->
      <section v-if="editModifyResult.length > 0" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num edit-num">4</span>
          <span class="step-title">修改结果</span>
          <span class="selected-count">共 {{ editModifyResult.length }} 个文件被修改</span>
        </div>
        <div class="step-body">
          <div class="gen-file-list">
            <div v-for="(file, idx) in editModifyResult" :key="idx" class="gen-file-item" :class="{ active: editCodeSelectedFile === idx }" @click="editCodeSelectedFile = idx">
              <span class="gen-file-icon">📄</span>
              <span class="gen-file-name">{{ file.filename }}</span>
            </div>
          </div>
          <div v-if="editCodeSelectedFile >= 0 && editModifyResult[editCodeSelectedFile]" class="terminal-container">
            <div class="terminal-header">
              <div class="terminal-dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
              <span class="terminal-title">{{ editModifyResult[editCodeSelectedFile].filename }}</span>
              <div class="terminal-actions">
                <el-button text size="small" @click="copyCurrentModified">📋 复制修改后代码</el-button>
              </div>
            </div>
            <div class="diff-container">
              <div class="diff-side">
                <div class="diff-label">原始代码</div>
                <pre class="diff-code original"><code>{{ editModifyResult[editCodeSelectedFile].original }}</code></pre>
              </div>
              <div class="diff-divider"></div>
              <div class="diff-side">
                <div class="diff-label">修改后</div>
                <pre class="diff-code fixed"><code>{{ editModifyResult[editCodeSelectedFile].modified }}</code></pre>
              </div>
            </div>
          </div>
          <div class="gen-actions">
            <el-button type="success" size="large" @click="downloadModifiedZip">
              📥 下载修改后的 ZIP
            </el-button>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 管理后台 Tab ============ -->
            <!-- ============ 项目中心 Tab ============ -->
    <main v-if="activeTab === 'projects'" class="main-content">
      <section class="step-section">
        <div class="step-header">
          <span class="step-num">📦</span>
          <span class="step-title">项目中心</span>
          <span style="margin-left: auto; font-size: 12px; color: var(--text-secondary);">共 {{ projectsData.length }} 个项目</span>
        </div>
        <div class="step-body">
          <!-- Project Stats -->
          <div class="projects-stats">
            <div class="project-stat-card">
              <div class="project-stat-value">{{ projectsData.length }}</div>
              <div class="project-stat-label">总项目数</div>
            </div>
            <div class="project-stat-card">
              <div class="project-stat-value" style="color: var(--accent-green)">{{ projectsData.filter(p => p.status === 'running').length }}</div>
              <div class="project-stat-label">运行中</div>
            </div>
            <div class="project-stat-card">
              <div class="project-stat-value" style="color: var(--accent-blue)">{{ projectsData.filter(p => p.type === 'Docker').length }}</div>
              <div class="project-stat-label">Docker</div>
            </div>
            <div class="project-stat-card">
              <div class="project-stat-value" style="color: var(--accent-purple)">{{ projectsData.filter(p => p.type === 'Cloudflare').length }}</div>
              <div class="project-stat-label">Cloudflare</div>
            </div>
          </div>
          
          <!-- Projects List -->
          <div class="projects-list">
            <div v-for="project in projectsData" :key="project.id" class="project-item">
              <div class="project-item-header">
                <span class="project-item-name">{{ project.name }}</span>
                <span class="project-item-status" :class="project.status">
                  {{ project.status === 'running' ? '运行中' : '已停止' }}
                </span>
              </div>
              <div class="project-item-info">
                <span v-if="project.domain">🌐 {{ project.domain }}</span>
                <span v-if="project.repo">📁 {{ project.repo }}</span>
                <span v-if="project.port">🔌 {{ project.port }}</span>
                <span>📋 {{ project.type }}</span>
              </div>
              <div class="project-item-desc">{{ project.desc }}</div>
            </div>
          </div>
        </div>
      </section>
    </main>

<!-- ============ 配置生成 Tab ============ -->
    <main v-if="activeTab === 'skills'" class="main-content">
      <section class="step-section">
        <div class="step-header">
          <span class="step-num">🛠</span>
          <span class="step-title">配置生成技能</span>
        </div>
        <div class="step-body">
          <p style="color: var(--text-secondary); margin-bottom: 20px; font-size: 14px;">
            选择以下技能，输入项目描述或需求，AI 将自动生成对应的配置文件。
          </p>
          
          <!-- Skills Grid -->
          <div class="skills-grid">
            <div v-for="skill in configSkills" :key="skill.id" 
                 class="skill-card" 
                 :class="{ active: selectedSkill === skill.id }"
                 @click="selectSkill(skill)">
              <div class="skill-card-icon">{{ skill.icon }}</div>
              <div class="skill-card-name">{{ skill.name }}</div>
              <div class="skill-card-desc">{{ skill.description }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Skill Execution Panel -->
      <section v-if="selectedSkill" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">{{ currentSkillMeta.icon }}</span>
          <span class="step-title">{{ currentSkillMeta.name }}</span>
        </div>
        <div class="step-body">
          <div class="skill-input-area">
            <el-input
              v-model="skillInputText"
              type="textarea"
              :rows="5"
              :placeholder="currentSkillMeta.placeholder"
              style="width: 100%;"
            />
          </div>
          <div style="margin-top: 16px; display: flex; gap: 12px; align-items: center;">
            <el-button type="primary" :loading="skillExecuting" @click="executeSkill" size="large">
              {{ skillExecuting ? '生成中...' : '🚀 开始生成' }}
            </el-button>
            <el-button @click="selectedSkill = ''; skillResult = ''" size="large">取消</el-button>
          </div>
        </div>
      </section>

      <!-- Skill Result -->
      <section v-if="skillResult" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num">✅</span>
          <span class="step-title">生成结果</span>
        </div>
        <div class="step-body">
          <div class="skill-result-area">
            <div class="result-actions">
              <el-button size="small" @click="copySkillResult">📋 复制</el-button>
              <el-button size="small" @click="downloadSkillResult">💾 下载</el-button>
            </div>
            <pre class="skill-result-code">{{ skillResult }}</pre>
          </div>
        </div>
      </section>
    </main>

<main v-if="activeTab === 'admin' && isAdmin" class="main-content">
      <!-- Admin Sub-tabs -->
      <div class="admin-subtabs">
        <button class="subtab-btn" :class="{ active: adminSubTab === 'dashboard' }" @click="adminSubTab = 'dashboard'; loadAdminStats()">📊 仪表盘</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'users' }" @click="adminSubTab = 'users'; loadAdminUsers()">👥 用户管理</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'orders' }" @click="adminSubTab = 'orders'; loadAdminOrders()">📋 订单管理</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'logs' }" @click="adminSubTab = 'logs'; loadDeployLogs()">📝 部署日志</button>
        <button class="subtab-btn" :class="{ active: adminSubTab === 'config' }" @click="adminSubTab = 'config'">⚙️ 系统配置</button>
      </div>

      <!-- Dashboard -->
      <section v-if="adminSubTab === 'dashboard'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">📊</span>
          <span class="step-title">数据概览</span>
        </div>
        <div class="step-body">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-info">
                <div class="stat-value">{{ adminStats.total_users }}</div>
                <div class="stat-label">总用户数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">💎</div>
              <div class="stat-info">
                <div class="stat-value">{{ adminStats.paid_users }}</div>
                <div class="stat-label">付费用户</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📈</div>
              <div class="stat-info">
                <div class="stat-value">{{ paidRate }}%</div>
                <div class="stat-label">付费率</div>
              </div>
            </div>
            <div class="stat-card accent-orange">
              <div class="stat-icon">💰</div>
              <div class="stat-info">
                <div class="stat-value">¥{{ adminStats.monthly_income }}</div>
                <div class="stat-label">本月收入</div>
              </div>
            </div>
            <div class="stat-card accent-blue">
              <div class="stat-icon">💵</div>
              <div class="stat-info">
                <div class="stat-value">¥{{ adminStats.total_income }}</div>
                <div class="stat-label">总收入</div>
              </div>
            </div>
            <div class="stat-card accent-green">
              <div class="stat-icon">📦</div>
              <div class="stat-info">
                <div class="stat-value">{{ adminStats.total_orders }}</div>
                <div class="stat-label">总订单</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Users Management -->
      <section v-if="adminSubTab === 'users'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">👥</span>
          <span class="step-title">用户管理</span>
          <span class="selected-count">{{ adminUsers.length }} 位用户</span>
        </div>
        <div class="step-body">
          <el-input v-model="userSearchQuery" placeholder="搜索用户 ID..." size="default" clearable style="margin-bottom: 16px; max-width: 300px;">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <div class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>用户 ID</th>
                  <th>付费类型</th>
                  <th>付费时间</th>
                  <th>到期时间</th>
                  <th>注册时间</th>
                  <th>管理员</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.user_id">
                  <td class="user-id-cell">{{ user.user_id }}</td>
                  <td>
                    <el-tag :type="userPaidTypeTag(user.paid_type)" size="small" effect="dark">
                      {{ userPaidTypeLabel(user.paid_type) }}
                    </el-tag>
                  </td>
                  <td class="time-cell">{{ formatTime(user.paid_at) }}</td>
                  <td class="time-cell">{{ formatTime(user.expires_at) }}</td>
                  <td class="time-cell">{{ formatTime(user.created_at) }}</td>
                  <td>
                    <el-tag v-if="user.is_admin" type="danger" size="small" effect="dark">Admin</el-tag>
                    <span v-else class="dim">-</span>
                  </td>
                  <td>
                    <el-dropdown trigger="click" @command="(cmd) => handleUserAction(user, cmd)">
                      <el-button size="small" type="primary" text>操作</el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="free">设为免费</el-dropdown-item>
                          <el-dropdown-item command="monthly">设为月付</el-dropdown-item>
                          <el-dropdown-item command="yearly">设为年付</el-dropdown-item>
                          <el-dropdown-item command="permanent">设为永久</el-dropdown-item>
                          <el-dropdown-item divided :command="user.is_admin ? 'revoke_admin' : 'grant_admin'">
                            {{ user.is_admin ? '取消管理员' : '设为管理员' }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Orders Management -->
      <section v-if="adminSubTab === 'orders'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">📋</span>
          <span class="step-title">订单管理</span>
          <span class="selected-count">{{ adminOrders.length }} 笔订单</span>
        </div>
        <div class="step-body">
          <div class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>订单 ID</th>
                  <th>用户</th>
                  <th>金额</th>
                  <th>套餐</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>支付时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="order in adminOrders" :key="order.order_id">
                  <td class="user-id-cell">{{ order.order_id }}</td>
                  <td class="user-id-cell">{{ order.user_id }}</td>
                  <td class="amount-cell">¥{{ order.amount }}</td>
                  <td>{{ planTypeLabel(order.paid_type) }}</td>
                  <td>
                    <el-tag :type="order.status === 'paid' ? 'success' : 'warning'" size="small" effect="dark">
                      {{ order.status === 'paid' ? '已支付' : '待支付' }}
                    </el-tag>
                  </td>
                  <td class="time-cell">{{ formatTime(order.created_at) }}</td>
                  <td class="time-cell">{{ formatTime(order.paid_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Deploy Logs -->
      <section v-if="adminSubTab === 'logs'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">📝</span>
          <span class="step-title">部署日志</span>
        </div>
        <div class="step-body">
          <div v-if="deployLogs.length === 0" class="empty-state">
            <span>📝</span>
            <p>暂无部署日志</p>
          </div>
          <div v-else class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>用户</th>
                  <th>项目</th>
                  <th>部署方式</th>
                  <th>状态</th>
                  <th>信息</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in deployLogs" :key="log.id">
                  <td class="user-id-cell">{{ log.user_id }}</td>
                  <td>{{ log.project_name }}</td>
                  <td>{{ log.deploy_type }}</td>
                  <td>
                    <el-tag :type="logStatusTag(log.status)" size="small" effect="dark">{{ log.status }}</el-tag>
                  </td>
                  <td class="msg-cell">{{ log.message }}</td>
                  <td class="time-cell">{{ formatTime(log.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Credit Logs -->
      <section v-if="adminSubTab === 'credits'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">💎</span>
          <span class="step-title">积分流水</span>
        </div>
        <div class="step-body">
          <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <el-input v-model="adminCreditUserId" placeholder="输入用户ID筛选" size="default" clearable style="width: 280px;" />
            <el-button size="default" @click="loadCreditLogs">查询</el-button>
            <el-divider direction="vertical" />
            <el-input v-model="adminAddCreditUserId" placeholder="用户ID" size="default" style="width: 200px;" />
            <el-input-number v-model="adminAddCreditAmount" :min="1" :step="1000" size="default" style="width: 140px;" />
            <el-input v-model="adminAddCreditDesc" placeholder="备注" size="default" style="width: 140px;" />
            <el-button type="warning" size="default" @click="adminAddCredits" :loading="adminAddCreditLoading">手动加积分</el-button>
          </div>
          <div v-if="creditLogs.length === 0" class="empty-state">
            <span>💎</span>
            <p>暂无积分流水</p>
          </div>
          <div v-else class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>用户</th>
                  <th>变动</th>
                  <th>类型</th>
                  <th>说明</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in creditLogs" :key="log.id">
                  <td class="user-id-cell">{{ log.user_id }}</td>
                  <td :style="{ color: log.amount > 0 ? '#3fb950' : '#f85149', fontWeight: 600 }">
                    {{ log.amount > 0 ? '+' : '' }}{{ log.amount.toLocaleString() }}
                  </td>
                  <td>
                    <el-tag :type="{'recharge': 'success', 'consume': 'warning', 'gift': 'info'}[log.type]" size="small" effect="dark">
                      {{ {'recharge': '充值', 'consume': '消费', 'gift': '赠送'}[log.type] || log.type }}
                    </el-tag>
                  </td>
                  <td class="msg-cell">{{ log.description || '-' }}</td>
                  <td class="time-cell">{{ formatTime(log.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

<!-- System Config -->
      <section v-if="adminSubTab === 'config'" class="step-section fade-in">
        <div class="step-header">
          <span class="step-num admin-num">⚙️</span>
          <span class="step-title">系统配置</span>
        </div>
        <div class="step-body">
          <div class="config-section">
            <h4>💎 积分套餐配置</h4>
            <div class="info-grid" style="margin-top: 12px;">
              <div class="info-item"><span class="info-label">体验包</span><span class="info-value">¥9.9 → 30,000 积分</span></div>
              <div class="info-item"><span class="info-label">基础包</span><span class="info-value">¥29 → 90,000 积分</span></div>
              <div class="info-item"><span class="info-label">进阶包</span><span class="info-value">¥99 → 300,000 积分</span></div>
              <div class="info-item"><span class="info-label">旗舰包</span><span class="info-value">¥299 → 900,000 积分</span></div>
            </div>
            <div class="info-grid" style="margin-top: 12px;">
              <div class="info-item"><span class="info-label">生成项目</span><span class="info-value">500 积分/次</span></div>
              <div class="info-item"><span class="info-label">修改代码</span><span class="info-value">300 积分/次</span></div>
              <div class="info-item"><span class="info-label">代码检测+修复</span><span class="info-value">200 积分/次</span></div>
              <div class="info-item"><span class="info-label">部署</span><span class="info-value">免费</span></div>
            </div>
          </div>
          <div class="config-section">
            <h4>🔑 管理员 Token</h4>
            <div class="config-form">
              <div class="config-form-item">
                <label>当前 Token</label>
                <el-input v-model="adminToken" type="password" show-password size="default" style="width: 300px;" placeholder="设置管理员 Token" />
              </div>
            </div>
            <p class="config-hint">通过请求头 <code>X-Admin-Token</code> 验证管理员身份</p>
          </div>
          <div class="config-section">
            <h4>📊 数据库信息</h4>
            <div class="info-grid" style="margin-top: 12px;">
              <div class="info-item"><span class="info-label">用户总数</span><span class="info-value">{{ adminStats.total_users }}</span></div>
              <div class="info-item"><span class="info-label">付费用户</span><span class="info-value">{{ adminStats.paid_users }}</span></div>
              <div class="info-item"><span class="info-label">总订单数</span><span class="info-value">{{ adminStats.total_orders }}</span></div>
              <div class="info-item"><span class="info-label">已支付订单</span><span class="info-value">{{ adminStats.paid_orders }}</span></div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- ============ 付费弹窗 ============ -->
    <el-dialog v-model="paymentDialogVisible" title="💎 充值积分" width="640px" :close-on-click-modal="false" class="payment-dialog">
      <div class="payment-content">
        <div style="text-align: center; margin-bottom: 16px; color: var(--text-secondary); font-size: 14px;">
          当前余额：<span style="color: var(--accent-orange); font-weight: 700; font-size: 18px;">💎 {{ formatCredits(userCredits) }}</span>
          <span style="margin-left: 12px; font-size: 12px;">（1元 = 3,000 积分）</span>
        </div>
        <div class="payment-plans credit-packages">
          <div v-for="pkg in creditPackages" :key="pkg.key" class="plan-card" :class="{ selected: selectedPackage === pkg.key, recommend: pkg.recommend }" @click="selectedPackage = pkg.key">
            <div v-if="pkg.recommend" class="plan-badge">推荐</div>
            <div class="plan-name">{{ pkg.label }}</div>
            <div class="plan-price">
              <span class="price-symbol">¥</span>
              <span class="price-num">{{ pkg.price }}</span>
            </div>
            <div class="plan-credits">💎 {{ pkg.credits.toLocaleString() }} 积分</div>
            <div class="plan-desc">{{ pkg.desc }}</div>
          </div>
        </div>
        <div class="payment-features">
          <div class="feature-item"><span class="feat-check">✓</span> 生成项目：500 积分/次</div>
          <div class="feature-item"><span class="feat-check">✓</span> 修改代码：300 积分/次</div>
          <div class="feature-item"><span class="feat-check">✓</span> 代码检测+AI修复：200 积分/次</div>
          <div class="feature-item"><span class="feat-check">✓</span> 部署脚本生成 & 远程部署：免费</div>
          <div class="feature-item"><span class="feat-check">✓</span> 积分永不过期</div>
        </div>
      </div>
      <template #footer>
        <div class="payment-footer">
          <el-button type="primary" size="large" :loading="payLoading" @click="handlePay" style="width: 200px;">
            立即购买
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ============ 登录/注册弹窗 ============ -->
    <el-dialog v-model="loginDialogVisible" :title="loginMode === 'login' ? '登录' : '注册'" width="420px" :close-on-click-modal="false">
      <div class="login-content">
        <el-form :model="loginForm" label-width="0" size="large">
          <el-form-item>
            <el-input v-model="loginForm.username" placeholder="用户名" clearable>
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-input v-model="loginForm.password" type="password" placeholder="密码" show-password>
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item v-if="loginMode === 'register'">
            <el-input v-model="loginForm.confirmPassword" type="password" placeholder="确认密码" show-password>
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>
        </el-form>
        <div class="login-actions">
          <el-button type="primary" :loading="loginLoading" @click="handleLogin" style="width: 100%;">
            {{ loginMode === 'login' ? '登录' : '注册' }}
          </el-button>
        </div>
        <div class="login-switch">
          <span v-if="loginMode === 'login'">
            还没有账号？<el-link type="primary" @click="loginMode = 'register'">立即注册</el-link>
          </span>
          <span v-else>
            已有账号？<el-link type="primary" @click="loginMode = 'login'">去登录</el-link>
          </span>
        </div>
      </div>
    </el-dialog>

    <!-- Admin Login Dialog -->
    <el-dialog v-model="adminLoginVisible" title="管理员验证" width="400px" :close-on-click-modal="false">
      <div class="admin-login-content">
        <p style="margin-bottom: 16px; color: var(--text-secondary); font-size: 14px;">请输入管理员 Token 以访问管理后台</p>
        <el-input v-model="adminTokenInput" type="password" show-password placeholder="输入管理员 Token" size="large" @keyup.enter="verifyAdminToken" />
      </div>
      <template #footer>
        <el-button @click="adminLoginVisible = false">取消</el-button>
        <el-button type="primary" @click="verifyAdminToken">验证</el-button>
      </template>
    </el-dialog>

    <!-- Edit User Dialog -->
    <el-dialog v-model="editUserDialogVisible" title="修改用户付费状态" width="420px">
      <div v-if="editingUser" style="margin-bottom: 16px;">
        <p style="color: var(--text-secondary); font-size: 14px;">用户: <code>{{ editingUser.user_id }}</code></p>
      </div>
      <el-form label-width="80px">
        <el-form-item label="付费类型">
          <el-select v-model="editUserForm.paid_type" style="width: 100%;">
            <el-option value="free" label="免费用户" />
            <el-option value="monthly" label="月度会员" />
            <el-option value="yearly" label="年度会员" />
            <el-option value="permanent" label="永久会员" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期时间" v-if="editUserForm.paid_type !== 'free' && editUserForm.paid_type !== 'permanent'">
          <el-date-picker v-model="editUserForm.expires_at" type="datetime" placeholder="选择到期时间" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editUserDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editUserLoading" @click="confirmEditUser">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- Save to Server Dialog -->
    <el-dialog v-model="saveToServerVisible" title="🖥️ 保存到服务器" width="480px" :close-on-click-modal="false">
      <div v-if="servers.length === 0" style="text-align:center; padding: 20px 0;">
        <p style="color: var(--text-secondary); margin-bottom: 16px;">暂无已配置的服务器</p>
        <p style="color: var(--accent-orange); font-size: 13px;">请先去「免费部署」tab 配置服务器信息</p>
      </div>
      <div v-else>
        <div style="margin-bottom: 16px;">
          <label style="font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 8px;">选择服务器</label>
          <el-select v-model="saveServerId" placeholder="选择已配置的服务器" size="large" style="width:100%">
            <el-option v-for="(s, i) in servers" :key="i" :value="String(i)" :label="`${s.name} (${s.host})`" />
          </el-select>
        </div>
        <div style="margin-bottom: 16px;">
          <label style="font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 8px;">目标路径</label>
          <el-input v-model="saveTargetPath" placeholder="/www/wwwroot/my-project/" size="large" />
          <p style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">文件将保存到此目录下，目录不存在会自动创建</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="saveToServerVisible = false">取消</el-button>
        <el-button type="primary" :loading="saveToServerLoading" :disabled="servers.length === 0 || !saveTargetPath.trim()" @click="doSaveToServer">确认保存</el-button>
      </template>
    </el-dialog>

    <!-- Footer -->
    <footer class="app-footer">
      <span>AI Auto Deploy</span>
      <span class="separator">·</span>
      <span>智能识别 · 一键部署 · 代码检测 · 自动修复 · AI 生成</span>
    </footer>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      activeTab: 'deploy',
      // PWA
      showInstallBtn: false,
      deferredPrompt: null,
      // User & Payment
      userId: localStorage.getItem('user_id') || 'user_' + Math.random().toString(36).slice(2, 10),
      paymentStatus: { paid: false, paid_type: 'free' },
      paymentDialogVisible: false,
      payLoading: false,
      // selectedPlan removed - using selectedPackage
      creditPackages: [
        { key: 'starter', label: '体验包', price: 9.9, credits: 30000, desc: '约60次生成', recommend: false },
        { key: 'basic', label: '基础包', price: 29, credits: 90000, desc: '约180次生成', recommend: false },
        { key: 'pro', label: '进阶包', price: 99, credits: 300000, desc: '约600次生成', recommend: true },
        { key: 'ultimate', label: '旗舰包', price: 299, credits: 900000, desc: '约1800次生成', recommend: false },
      ],
      selectedPackage: 'pro',
      userCredits: 0,
      // paymentFeatures removed - credit-based system
      // Login/Register
      loginDialogVisible: false,
      loginMode: 'login', // 'login' or 'register'
      loginLoading: false,
      loginForm: { username: '', password: '', confirmPassword: '' },
      isLoggedIn: !!localStorage.getItem('user_id'),
      loggedInUsername: localStorage.getItem('logged_in_username') || '',
      // SSH Connection
      sshForm: { host: '', port: 22, username: 'root', password: '' },
      sshConnecting: false,
      sshSessionId: null,
      sshHostInfo: '',
      sshConnected: false,
      scanningPaths: false,
      // Deploy tab
      availablePaths: [],
      guideExpanded: true,
      projectPath: '',
      deployMode: 'server',
      deployUploadFile: null,
      deployTempDir: '',
      deploySshCollapsed: true,
      projectInfo: null,
      detecting: false,
      generating: false,
      deployType: 'local',
      selectedServerIdx: 0,
      domain: '',
      servers: [],
      scriptOutput: '',
      scriptFilename: '',
      extraFiles: [],
      copied: false,
      deployOptions: [
        { value: 'local', label: '本地脚本', icon: '📝' },
        { value: 'server', label: '云服务器 (SSH)', icon: '🖥️' },
        { value: 'cloudflare', label: 'Cloudflare Pages', icon: '☁️' },
        { value: 'docker', label: 'Docker', icon: '🐳' },
      ],
      // Remote deploy
      remoteDeploying: false,
      remoteLogs: [],
      remoteStatus: '',
      // Generate tab
      genDescription: '',
      genProjectType: 'frontend',
      genTechStack: 'vue3',
      genLoading: false,
      genFiles: [],
      genSelectedFile: -1,
      techStacks: {
        frontend: {
          vue3: { label: 'Vue 3 + Vite', desc: 'Vue 3 组合式 API + Vite 构建工具' },
          react: { label: 'React 18', desc: 'React 18 + Hooks + Vite' },
          html: { label: '原生 HTML/CSS/JS', desc: '纯前端，无框架依赖' },
        },
        backend: {
          fastapi: { label: 'FastAPI', desc: 'Python 异步框架' },
          flask: { label: 'Flask', desc: 'Python 轻量级框架' },
          express: { label: 'Express.js', desc: 'Node.js 框架' },
        },
        fullstack: {
          nextjs: { label: 'Next.js', desc: 'React 全栈框架' },
          nuxtjs: { label: 'Nuxt.js', desc: 'Vue 全栈框架' },
        },
      },
      // Fix tab
      fixMode: 'remote',  // 'remote' | 'upload'
      fixProjectPath: '',
      fixServerId: '',
      fixUploadFile: null,
      fixTempDir: '',
      analyzing: false,
      analysisResult: null,
      selectedErrors: [],
      repairing: false,
      repairResults: [],
      // Save to server
      saveToServerVisible: false,
      saveServerId: '',
      saveTargetPath: '',
      saveToServerLoading: false,
      // User Profile
      userProfile: {},
      userProfileLoaded: false,
      // Edit Code tab (AI Code Modifier)
      // Admin
      isAdmin: false,
      adminSubTab: 'dashboard',
      logoClickCount: 0,
      // 项目中心数据
      projectsData: [
    { id: 'ai-staff', name: 'AI智能体工作台', domain: 'www.zhinenti.cn', repo: 'hpennn/ai-staff', type: 'Docker', port: '8000:8000', status: 'running', desc: '多角色AI助手平台，支持技能/工作流自定义', dockerName: 'ai-staff' },
    { id: 'ai-auto-deploy', name: 'AI自动部署', domain: 'auto.zhinenti.cn', repo: 'hpennn/ai-auto-deploy', type: 'Docker', port: '8001:8000', status: 'running', desc: '积分消耗制自动部署工具', dockerName: 'ai-auto-deploy' },
    { id: 'deploy-easy', name: '智能部署助手', domain: 'deploy.zhinenti.cn', repo: 'hpennn/deploy-easy', type: 'Docker', port: '8003:8000', status: 'running', desc: '一键生成Docker/Nginx/部署配置', dockerName: 'deploy-easy' },
    { id: 'marketing-craft', name: '智能营销助手', domain: 'craft.zhinenti.cn', repo: 'hpennn/marketing-craft', type: 'Docker', port: '8004:8000', status: 'running', desc: '智能营销内容生成器', dockerName: 'marketing-craft' },
    { id: 'ecom-bot', name: '电商客服机器人', domain: 'zhinenti.cn:8000', repo: 'hpennn/ecom-bot', type: 'Docker', port: '8002:8000', status: 'running', desc: '电商智能客服，接入虎皮椒支付', dockerName: 'ecom-bot' },
    { id: 'kuaisu-tools', name: '快速工具箱', domain: 'www.kuaisu.online', repo: 'hpennn/kuaisu-tools', type: 'Cloudflare', port: '', status: 'running', desc: '在线工具合集' },
    { id: 'ocr-tool', name: 'OCR识别工具', domain: 'ocr.hpenn.xyz', repo: 'hpennn/ocr-tool', type: 'Cloudflare', port: '', status: 'running', desc: 'AI图片文字识别' },
    { id: 'ai-nav', name: 'AI导航站', domain: 'www.hpennn.online', repo: 'hpennn/ai-nav', type: 'Cloudflare', port: '', status: 'running', desc: 'AI工具导航聚合' },
    { id: 'ai-resume', name: 'AI简历生成', domain: 'resume.hpenn.xyz', repo: 'hpennn/ai-resume', type: 'Cloudflare', port: '', status: 'running', desc: 'AI驱动简历制作' },
    { id: 'image-tools', name: '图片处理工具', domain: 'www.kuaisutupo.xyz', repo: 'hpennn/image-tools', type: 'Cloudflare', port: '', status: 'running', desc: '图片压缩/格式转换/裁剪' },
    { id: 'doc-summary', name: '文档摘要工具', domain: 'doc.hpenn.xyz', repo: 'hpennn/doc-summary', type: 'Cloudflare', port: '', status: 'running', desc: 'PDF/Word文档智能摘要' },
    { id: 'text-tools', name: '文本处理工具', domain: 'www.hpenn.xyz', repo: 'hpennn/text-tools', type: 'Cloudflare', port: '', status: 'running', desc: '文本转换/格式化/分析' },
    { id: 'doc-convert', name: '文档格式转换', domain: 'convert.hpenn.xyz', repo: 'hpennn/doc-convert', type: 'Cloudflare', port: '', status: 'running', desc: 'PDF/Word/Excel格式互转' },
    { id: 'dev-tools', name: '开发者工具集', domain: 'www.hpennn.xyz', repo: 'hpennn/dev-tools', type: 'Cloudflare', port: '', status: 'running', desc: 'JSON格式化/Base64/正则测试等' },
    { id: 'table-gen', name: '表格生成器', domain: 'table.hpenn.xyz', repo: 'hpennn/table-gen', type: 'Cloudflare', port: '', status: 'running', desc: 'AI生成表格/数据转换' },
    { id: 'ai-blessing', name: 'AI祝福语', domain: 'www.zhinenti.vip', repo: 'hpennn/ai-blessing', type: 'Cloudflare', port: '', status: 'running', desc: 'AI生成个性化祝福语' },
    { id: 'ai-copywriter', name: 'AI文案写手', domain: 'www.zhinenti.xyz', repo: 'hpennn/ai-copywriter', type: 'Cloudflare', port: '', status: 'running', desc: 'AI营销文案生成' },
    { id: 'batch-img-edit', name: '批量图片编辑', domain: 'imgedit.hpenn.xyz', repo: 'hpennn/batch-img-edit', type: 'Cloudflare', port: '', status: 'running', desc: '批量水印/裁剪/压缩' },
    { id: 'ai-naming', name: 'AI起名助手', domain: 'www.hpenn.online', repo: 'hpennn/ai-naming', type: 'Cloudflare', port: '', status: 'running', desc: 'AI智能取名' },
    { id: 'ai-content-tools', name: 'AI内容工具', domain: 'content.hpennn.xyz', repo: 'hpennn/ai-content-tools', type: 'Cloudflare', port: '', status: 'running', desc: '内容创作/改写/翻译' },
    { id: 'ai-marketing-tools', name: 'AI营销工具', domain: 'marketing.hpennn.xyz', repo: 'hpennn/ai-marketing-tools', type: 'Cloudflare', port: '', status: 'running', desc: '营销策略/SEO/社媒管理' },
    { id: 'ai-ppt-report', name: 'AI PPT报告', domain: 'ppt.hpennn.xyz', repo: 'hpennn/ai-ppt-report', type: 'Cloudflare', port: '', status: 'running', desc: 'AI生成PPT/报告' },
    { id: 'social-publisher', name: '社媒发布器', domain: 'publish.hpennn.xyz', repo: 'hpennn/social-publisher', type: 'Cloudflare', port: '', status: 'running', desc: '多平台内容一键发布' },
    { id: 'smart-marketing', name: '智慧营销', domain: 'smart.hpennn.xyz', repo: 'hpennn/smart-marketing', type: 'Cloudflare', port: '', status: 'running', desc: '智能营销自动化' }
],
      // Skills (配置生成)
      selectedSkill: '',
      skillInputText: '',
      skillResult: '',
      skillExecuting: false,
      configSkills: [
        { id: 'dockerfile_gen', name: 'Dockerfile生成', icon: '🐳', description: '根据应用描述生成优化的多阶段Dockerfile', placeholder: '描述你的应用，例如：一个使用 Python 3.11 的 FastAPI 应用，需要连接 PostgreSQL 数据库...' },
        { id: 'docker_compose', name: 'Docker Compose', icon: '🐳', description: '生成完整的docker-compose.yml编排配置', placeholder: '描述你的多容器应用架构，例如：一个Web应用 + Redis缓存 + MySQL数据库...' },
        { id: 'nginx_config', name: 'Nginx配置', icon: '🌐', description: '生成Nginx反向代理、SSL、负载均衡配置', placeholder: '描述你的Nginx配置需求，例如：为 myapp.com 配置反向代理到 8000 端口，启用 HTTPS...' },
        { id: 'deploy_script', name: '部署脚本', icon: '🚀', description: '生成自动化部署Shell脚本', placeholder: '描述你的部署需求，例如：将 Node.js 应用部署到 Ubuntu 服务器，使用 PM2 管理...' },
        { id: 'env_config', name: '环境变量', icon: '🔑', description: '生成环境变量模板和安全配置', placeholder: '描述你的环境变量需求，例如：为一个 Web 应用生成生产环境变量配置...' },
        { id: 'ssl_setup', name: 'SSL证书', icon: '🔒', description: '生成SSL证书配置和HTTPS设置', placeholder: '描述你的SSL需求，例如：为 example.com 配置 Let\'s Encrypt 免费SSL证书...' },
        { id: 'ci_cd', name: 'CI/CD流水线', icon: '🔄', description: '生成GitHub Actions或GitLab CI配置', placeholder: '描述你的CI/CD需求，例如：为 Node.js 项目配置 GitHub Actions 自动测试和部署...' },
        { id: 'db_setup', name: '数据库配置', icon: '🗄️', description: '生成数据库初始化SQL、权限配置和备份脚本', placeholder: '描述你的数据库需求，例如：创建一个 MySQL 数据库，设置用户权限和自动备份...' },
      ],
      editZipFile: null,
      editCodeDescription: '',
      editModifyResult: [],
      editCodeSelectedFile: -1,
      editCodeLoading: false,
      adminLoginVisible: false,
      adminTokenInput: '',
      adminToken: '',
      adminStats: { total_users: 0, paid_users: 0, free_users: 0, monthly_income: 0, total_income: 0, total_orders: 0, paid_orders: 0 },
      adminUsers: [],
      adminOrders: [],
      deployLogs: [],
      userSearchQuery: '',
      editUserDialogVisible: false,
      editUserLoading: false,
      editingUser: null,
      editUserForm: { paid_type: 'free', expires_at: null },
      creditLogs: [],
      adminCreditUserId: '',
      adminAddCreditUserId: '',
      adminAddCreditAmount: 1000,
      adminAddCreditDesc: '',
      adminAddCreditLoading: false,
    }
  },
  computed: {
    currentStacks() {
      return this.techStacks[this.genProjectType] || {}
    },
    // planLabel removed - credit-based system
    paidRate() {
      if (this.adminStats.total_users === 0) return 0
      return ((this.adminStats.paid_users / this.adminStats.total_users) * 100).toFixed(1)
    },
    filteredUsers() {
      if (!this.userSearchQuery) return this.adminUsers
      const q = this.userSearchQuery.toLowerCase()
      return this.adminUsers.filter(u => u.user_id.toLowerCase().includes(q))
    },
    // Old subscription computed properties removed
  },
  watch: {
    logoClickCount(val) {
      if (val >= 5 && !this.isAdmin) {
        this.logoClickCount = 0
        this.adminLoginVisible = true
      }
    },
  },
  mounted() {
    // Check for admin URL param
    const urlParams = new URLSearchParams(window.location.search)
    const adminParam = urlParams.get('admin')
    if (adminParam === '1') {
      this.adminLoginVisible = true
    }

    // Paths are now loaded after SSH connection, not on mount
    this.loadServers()
    this.checkPaymentStatus()
    this.checkAdminStatus()
    if (this.isLoggedIn) {
      this.loadUserProfile()
    }

    // PWA install prompt
    if (window.matchMedia('(display-mode: standalone)').matches) {
      this.showInstallBtn = false
    } else {
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault()
        this.deferredPrompt = e
        this.showInstallBtn = true
      })
    }
  },
  methods: {
    // ============ 配置生成技能 Methods ============
    selectSkill(skill) {
      this.selectedSkill = skill.id
      this.skillResult = ''
      this.skillInputText = ''
    },
    get currentSkillMeta() {
      return this.configSkills.find(s => s.id === this.selectedSkill) || {}
    },
    async executeSkill() {
      if (!this.skillInputText.trim()) {
        this.$message.warning('请输入描述信息')
        return
      }
      this.skillExecuting = true
      this.skillResult = ''
      try {
        const res = await axios.post(`/api/skills/${this.selectedSkill}/execute`, {
          text: this.skillInputText,
          user_id: this.userId
        })
        if (res.data && res.data.output) {
          this.skillResult = res.data.output.content || JSON.stringify(res.data.output, null, 2)
        } else if (res.data && res.data.error) {
          this.$message.error(res.data.error)
        }
      } catch (e) {
        if (e.response && e.response.status === 402) {
          this.$message.error('积分不足，请充值后使用')
          this.showPaymentDialog()
        } else {
          this.$message.error('生成失败: ' + (e.response?.data?.detail || e.message))
        }
      } finally {
        this.skillExecuting = false
      }
    },
    copySkillResult() {
      navigator.clipboard.writeText(this.skillResult).then(() => {
        this.$message.success('已复制到剪贴板')
      })
    },
    downloadSkillResult() {
      const skill = this.configSkills.find(s => s.id === this.selectedSkill)
      const filename = skill ? skill.id + '_output.txt' : 'skill_output.txt'
      const blob = new Blob([this.skillResult], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    },

    // ===== PWA =====
    async installPWA() {
      if (!this.deferredPrompt) return
      this.deferredPrompt.prompt()
      const { outcome } = await this.deferredPrompt.userChoice
      if (outcome === 'accepted') {
        this.showInstallBtn = false
      }
      this.deferredPrompt = null
    },
    // ===== Admin =====
    async checkAdminStatus() {
      try {
        const res = await axios.get('/api/admin/verify', {
          headers: { 'x-user-id': this.userId },
        })
        this.isAdmin = res.data.is_admin
      } catch {
        this.isAdmin = false
      }
    },
    async verifyAdminToken() {
      try {
        const res = await axios.get('/api/admin/verify', {
          headers: {
            'x-admin-token': this.adminTokenInput,
            'x-user-id': this.userId,
          },
        })
        if (res.data.is_admin) {
          this.isAdmin = true
          this.adminToken = this.adminTokenInput
          this.adminLoginVisible = false
          this.$message.success('管理员验证成功')
          this.loadAdminStats(); if (this.adminSubTab === 'credits') this.loadCreditLogs()
        } else {
          this.$message.error('Token 无效')
        }
      } catch {
        this.$message.error('验证失败')
      }
    },
    getAdminHeaders() {
      const headers = { 'x-user-id': this.userId }
      if (this.adminToken) {
        headers['x-admin-token'] = this.adminToken
      }
      return headers
    },
    async loadAdminStats() {
      try {
        const res = await axios.get('/api/admin/stats', { headers: this.getAdminHeaders() })
        this.adminStats = res.data
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async loadAdminUsers() {
      try {
        const res = await axios.get('/api/admin/users', { headers: this.getAdminHeaders() })
        this.adminUsers = res.data.users || []
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async loadAdminOrders() {
      try {
        const res = await axios.get('/api/admin/orders', { headers: this.getAdminHeaders() })
        this.adminOrders = res.data.orders || []
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async loadDeployLogs() {
      try {
        const res = await axios.get('/api/admin/logs', { headers: this.getAdminHeaders() })
        this.deployLogs = res.data.logs || []
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async handleUserAction(user, command) {
      if (command === 'grant_admin' || command === 'revoke_admin') {
        try {
          await axios.post('/api/admin/set-admin', {
            user_id: user.user_id,
            is_admin: command === 'grant_admin',
          }, { headers: this.getAdminHeaders() })
          this.$message.success(command === 'grant_admin' ? '已设为管理员' : '已取消管理员')
          await this.loadAdminUsers()
        } catch (err) {
          this.$message.error(err.response?.data?.detail || '操作失败')
        }
        return
      }
      // Open edit dialog for paid type changes
      this.editingUser = user
      this.editUserForm.paid_type = command || user.paid_type
      this.editUserForm.expires_at = null
      if (command && command !== 'free') {
        // Set default expiry based on plan type
        const now = new Date()
        if (command === 'monthly') now.setDate(now.getDate() + 30)
        else if (command === 'yearly') now.setDate(now.getDate() + 365)
        this.editUserForm.expires_at = now
      }

      // Quick update for simple commands
      if (command && ['free', 'monthly', 'yearly', 'permanent'].includes(command)) {
        this.editUserDialogVisible = true
      }
    },
    async confirmEditUser() {
      this.editUserLoading = true
      try {
        const expiresAt = this.editUserForm.expires_at
          ? new Date(this.editUserForm.expires_at).toISOString()
          : null

        await axios.put(`/api/admin/users/${this.editingUser.user_id}`, {
          paid_type: this.editUserForm.paid_type,
          expires_at: expiresAt,
        }, { headers: this.getAdminHeaders() })

        this.$message.success('用户状态已更新')
        this.editUserDialogVisible = false
        await this.loadAdminUsers()
        await this.loadAdminStats(); if (this.adminSubTab === 'credits') this.loadCreditLogs()
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '更新失败')
      } finally {
        this.editUserLoading = false
      }
    },
    userPaidTypeTag(type) {
      return { free: 'info', monthly: '', yearly: 'warning', permanent: 'danger' }[type] || 'info'
    },
    userPaidTypeLabel(type) {
      return { free: '免费', monthly: '月付', yearly: '年付', permanent: '永久' }[type] || type
    },
    planTypeLabel(type) {
      return { monthly: '月度会员', yearly: '年度会员', permanent: '永久会员' }[type] || type || '-'
    },
    formatTime(t) {
      if (!t) return '-'
      try {
        return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      } catch { return t }
    },
    logStatusTag(status) {
      return { success: 'success', failed: 'danger', error: 'danger', running: 'warning' }[status] || 'info'
    },
    // ===== Payment =====
    async checkPaymentStatus() {
      try {
        const res = await axios.get(`/api/payment/user/${this.userId}`)
        this.paymentStatus = {
          paid: (res.data.credits || 0) > 0,
          paid_type: res.data.paid_type || 'free',
          expires_at: res.data.expires_at,
        }
        this.userCredits = res.data.credits || 0
      } catch { /* ignore */ }
    },
    showPaymentDialog() {
      if (!this.isLoggedIn) {
        // 未登录，先弹出登录/注册弹窗
        this.loginMode = 'login'
        this.loginDialogVisible = true
        return
      }
      this.paymentDialogVisible = true
    },
    async handleLogin() {
      if (!this.loginForm.username.trim()) {
        this.$message.warning('请输入用户名')
        return
      }
      if (!this.loginForm.password) {
        this.$message.warning('请输入密码')
        return
      }
      if (this.loginMode === 'register' && this.loginForm.password !== this.loginForm.confirmPassword) {
        this.$message.warning('两次密码输入不一致')
        return
      }

      this.loginLoading = true
      try {
        const endpoint = this.loginMode === 'login' ? '/api/auth/login' : '/api/auth/register'
        const res = await axios.post(endpoint, {
          username: this.loginForm.username,
          password: this.loginForm.password,
        })
        if (res.data.success) {
          this.userId = res.data.user_id
          this.isLoggedIn = true
          this.loggedInUsername = this.loginForm.username
          localStorage.setItem('user_id', res.data.user_id)
          localStorage.setItem('logged_in_username', this.loginForm.username)
          this.$message.success(this.loginMode === 'login' ? '登录成功' : '注册成功')
          this.loginDialogVisible = false
          // 注册后清空表单
          this.loginForm = { username: '', password: '', confirmPassword: '' }
          // 加载用户详细信息
          this.loadUserProfile()
          this.checkPaymentStatus()
          this.checkAdminStatus()
          // 如果是从开通会员进来的，登录后自动打开支付弹窗
          if (this.loginMode === 'register') {
            setTimeout(() => { this.paymentDialogVisible = true }, 300)
          }
        } else {
          this.$message.error(res.data.message || '操作失败')
        }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '网络错误')
      } finally {
        this.loginLoading = false
      }
    },
    handleLogout() {
      this.isLoggedIn = false
      this.loggedInUsername = ''
      this.userId = 'user_' + Math.random().toString(36).slice(2, 10)
      this.isAdmin = false
      this.userProfile = {}
      this.userProfileLoaded = false
      localStorage.removeItem('user_id')
      localStorage.removeItem('logged_in_username')
      this.$message.success('已退出登录')
    },
    async handlePay() {
      this.payLoading = true
      try {
        const res = await axios.post('/api/payment/create', {
          user_id: this.userId,
          package: this.selectedPackage,
        })
        if (res.data.pay_url) {
          window.open(res.data.pay_url, '_blank')
          this.$message.info('请在新窗口完成支付，支付成功后积分自动到账')
          this.pollPaymentStatus(res.data.order_id)
        }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '创建支付失败')
      } finally {
        this.payLoading = false
      }
    },
    async pollPaymentStatus(orderId) {
      const maxRetries = 30
      for (let i = 0; i < maxRetries; i++) {
        await new Promise(r => setTimeout(r, 3000))
        try {
          const res = await axios.get(`/api/payment/check/${orderId}`)
          if (res.data.status === 'paid') {
            this.$message.success('支付成功！积分已到账')
            this.paymentDialogVisible = false
            await this.checkPaymentStatus()
            return
          }
        } catch { /* continue */ }
      }
      this.$message.info('支付确认中，请稍后刷新页面查看')
    },
    async requireCredits(cost, featureName) {
      if (this.userCredits >= cost) return true
      this.$message.warning(`积分不足，${featureName}需要 ${cost} 积分，当前余额 ${this.userCredits} 积分`)
      this.showPaymentDialog()
      return false
    },
    // ===== Deploy =====
    async connectServer() {
      if (!this.sshForm.host || !this.sshForm.password) {
        this.$message.warning('请填写服务器 IP 和密码')
        return
      }
      this.sshConnecting = true
      try {
        const res = await axios.post('/api/deploy/connect', {
          host: this.sshForm.host,
          port: this.sshForm.port || 22,
          username: this.sshForm.username || 'root',
          password: this.sshForm.password,
        })
        this.sshSessionId = res.data.session_id
        this.sshHostInfo = res.data.hostname || res.data.host
        this.sshConnected = true
        this.$message.success(res.data.message)
        // Auto scan remote paths after connection
        this.scanRemotePaths()
      } catch (err) {
        this.$message.error(err.response?.data?.detail || 'SSH 连接失败')
      } finally {
        this.sshConnecting = false
      }
    },
    async disconnectServer() {
      if (this.sshSessionId) {
        try {
          await axios.post('/api/deploy/disconnect?session_id=' + this.sshSessionId)
        } catch (e) { /* ignore */ }
      }
      this.sshSessionId = null
      this.sshConnected = false
      this.sshHostInfo = ''
      this.availablePaths = []
      this.projectPath = ''
      this.projectInfo = null
      this.scriptOutput = ''
      this.$message.info('已断开服务器连接')
    },
    async scanRemotePaths() {
      if (!this.sshSessionId) {
        this.$message.warning('请先连接服务器')
        return
      }
      this.scanningPaths = true
      try {
        const res = await axios.get('/api/deploy/list-paths?session_id=' + this.sshSessionId)
        this.availablePaths = res.data || []
        if (this.availablePaths.length === 0) {
          this.$message.info('远程服务器未找到项目目录')
        }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '扫描远程目录失败')
        this.availablePaths = []
      } finally {
        this.scanningPaths = false
      }
    },
    onPathSelect(val) {
      if (val) this.detectProject()
    },
    // === Deploy upload mode methods ===
    triggerDeployZipSelect() { this.$refs.deployZipInput.click(); },
    handleDeployZipSelect(e) {
      const file = e.target.files[0];
      if (file) {
        if (!file.name.toLowerCase().endsWith('.zip')) {
          this.$message.error('请选择 .zip 格式文件');
          return;
        }
        this.deployUploadFile = file;
      }
    },
    handleDeployZipDrop(e) {
      const file = e.dataTransfer.files[0];
      if (file) {
        if (!file.name.toLowerCase().endsWith('.zip')) {
          this.$message.error('请选择 .zip 格式文件');
          return;
        }
        this.deployUploadFile = file;
      }
    },
    async detectUploadedProject() {
      if (!this.deployUploadFile) {
        this.$message.warning('请先选择 ZIP 文件');
        return;
      }
      this.detecting = true;
      try {
        const formData = new FormData();
        formData.append('file', this.deployUploadFile);
        const res = await fetch('/api/deploy/upload-detect', {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || '上传检测失败');
        }
        const info = await res.json();
        this.projectInfo = info;
        this.projectPath = info.path || '';
        this.deployTempDir = info.temp_dir || '';
        if (info.recommend_deploy && this.deployOptions.some(o => o.value === info.recommend_deploy)) {
          this.deployType = info.recommend_deploy;
        }
        this.$message.success(`识别成功：${info.project_name} (${info.type})`);
      } catch (err) {
        this.$message.error(err.message || '上传检测失败');
      } finally {
        this.detecting = false;
      }
    },
    onDeployModeChange() {
      this.projectInfo = null;
      this.projectPath = '';
      this.scriptOutput = '';
      this.scriptFilename = '';
      this.extraFiles = [];
      this.deployUploadFile = null;
      this.deployTempDir = '';
      this.deployType = 'local';
    },
    async detectProject() {
      if (!this.projectPath.trim()) { this.$message.warning('请输入项目路径'); return }
      if (this.deployMode === 'remote' && !this.sshConnected) { this.$message.warning('请先连接远程服务器'); return }
      this.detecting = true
      this.projectInfo = null
      this.scriptOutput = ''
      try {
        const payload = { path: this.projectPath }
        if (this.sshSessionId) payload.session_id = this.sshSessionId
        const res = await axios.post('/api/deploy/detect', payload)
        this.projectInfo = res.data
        this.domain = res.data.project_name
        if (res.data.recommend_deploy && this.deployOptions.some(o => o.value === res.data.recommend_deploy)) {
          this.deployType = res.data.recommend_deploy
        }
        this.$message.success('项目检测完成')
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '检测失败')
      } finally { this.detecting = false }
    },
    async generateScript() {
      this.generating = true
      this.scriptOutput = ''
      this.extraFiles = []
      this.remoteLogs = []
      this.remoteStatus = ''
      try {
        const payload = { path: this.projectPath, deploy_type: this.deployType, domain: this.domain || undefined }
        if (this.sshSessionId) {
          payload.session_id = this.sshSessionId
        }
        if (this.deployType === 'server' && this.servers.length > 0) {
          payload.server = this.servers[this.selectedServerIdx]
        }
        const res = await axios.post('/api/deploy/generate', payload)
        this.scriptOutput = res.data.script
        this.scriptFilename = res.data.filename
        this.extraFiles = res.data.extra_files || []
        this.$message.success('脚本生成成功')
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '生成失败')
      } finally { this.generating = false }
    },
    async loadServers() {
      try {
        const res = await axios.get('/api/servers')
        this.servers = res.data.servers || []
      } catch { this.servers = [] }
    },
    async startRemoteDeploy() {
      // Deploy is free - no credit check needed
      if (!this.scriptOutput) { this.$message.warning('请先生成部署脚本'); return }

      this.remoteDeploying = true
      this.remoteLogs = []
      this.remoteStatus = 'connecting'

      try {
        const deployBody = {
          script: this.scriptOutput,
          project_path: this.projectPath,
        }
        if (this.sshSessionId) {
          deployBody.session_id = this.sshSessionId
        } else {
          deployBody.server_index = this.selectedServerIdx
        }
        const resp = await fetch('/api/deploy/remote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(deployBody),
        })

        const reader = resp.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              this.remoteLogs.push(line.slice(6))
              this.$nextTick(() => {
                const el = this.$refs.remoteLogBody
                if (el) el.scrollTop = el.scrollHeight
              })
            } else if (line.startsWith('event: done')) {
              this.remoteDeploying = false
            }
          }
        }

        const lastLog = this.remoteLogs[this.remoteLogs.length - 1] || ''
        if (lastLog.includes('🎉') || lastLog.includes('部署完成')) {
          this.remoteStatus = 'success'
        } else {
          this.remoteStatus = 'failed'
        }
      } catch (err) {
        this.remoteLogs.push(`❌ 连接错误: ${err.message}`)
        this.remoteStatus = 'error'
      } finally {
        this.remoteDeploying = false
      }
    },
    copyScript() {
      navigator.clipboard.writeText(this.scriptOutput)
      this.copied = true
      setTimeout(() => { this.copied = false }, 2000)
    },
    copyExtra(content) { navigator.clipboard.writeText(content); this.$message.success('已复制') },
    downloadScript() { this.downloadFile(this.scriptFilename, this.scriptOutput) },
    downloadExtra(file) { this.downloadFile(file.filename, file.content) },
    downloadFile(filename, content) {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
      URL.revokeObjectURL(url)
    },
    typeTagColor(type) { return { python: 'success', nodejs: 'warning', static: 'info' }[type] || '' },

    // ===== Generate =====
    onGenTypeOnChange() {
      const stacks = Object.keys(this.techStacks[this.genProjectType] || {})
      this.genTechStack = stacks[0] || ''
    },
    async generateProject() {
      if (!(await this.requireCredits(500, '生成项目'))) return
      if (!this.genDescription.trim()) { this.$message.warning('请输入项目描述'); return }

      this.genLoading = true
      this.genFiles = []
      this.genSelectedFile = -1
      try {
        const res = await axios.post('/api/generate/project', {
          description: this.genDescription,
          project_type: this.genProjectType,
          tech_stack: this.genTechStack,
          user_id: this.userId,
        })
        this.genFiles = res.data.files || []
        if (this.genFiles.length > 0) this.genSelectedFile = 0
        this.updateCreditsFromResponse(res)
        this.$message.success(`项目生成完成，共 ${this.genFiles.length} 个文件，消耗 500 积分`)
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '生成失败')
        }
      } finally { this.genLoading = false }
    },
    copyGenFile() {
      if (this.genSelectedFile >= 0 && this.genFiles[this.genSelectedFile]) {
        navigator.clipboard.writeText(this.genFiles[this.genSelectedFile].content)
        this.$message.success('已复制')
      }
    },
    async downloadGenProject() {
      try {
        const res = await axios.post('/api/generate/download', {
          files: this.genFiles,
          project_name: 'generated-project',
        }, { responseType: 'blob' })
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a'); a.href = url; a.download = 'generated-project.zip'; a.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        this.$message.error('下载失败')
      }
    },

    // ===== Code Fix =====
    triggerZipSelect() {
      this.$refs.zipInput.click()
    },
    handleZipSelect(e) {
      const file = e.target.files[0]
      if (file && file.name.endsWith('.zip')) {
        if (file.size > 5 * 1024 * 1024) {
          this.$message.warning('文件不能超过 5MB')
          return
        }
        this.editZipFile = file
      }
    },
    handleZipDrop(e) {
      const file = e.dataTransfer.files[0]
      if (file && file.name.endsWith('.zip')) {
        if (file.size > 5 * 1024 * 1024) {
          this.$message.warning('文件不能超过 5MB')
          return
        }
        this.editZipFile = file
      }
    },
    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / 1024 / 1024).toFixed(1) + ' MB'
    },
    async aiModifyProject() {
      if (!this.editZipFile) { this.$message.warning('请先上传项目源码'); return }
      if (!this.editCodeDescription.trim()) { this.$message.warning('请描述修改需求'); return }
      if (!(await this.requireCredits(300, '修改代码'))) return

      this.editCodeLoading = true
      this.editModifyResult = []
      this.editCodeSelectedFile = -1
      try {
        const formData = new FormData()
        formData.append('file', this.editZipFile)
        formData.append('description', this.editCodeDescription)
        if (this.userId) formData.append('user_id', this.userId)

        const res = await axios.post('/api/generate/modify-code', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.editModifyResult = res.data.files || []
        if (this.editModifyResult.length > 0) {
          this.editCodeSelectedFile = 0
          this.updateCreditsFromResponse(res)
          this.$message.success(`修改完成，共 ${this.editModifyResult.length} 个文件，消耗 300 积分`)
        } else {
          this.$message.info('AI 未检测到需要修改的内容')
        }
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '修改失败')
        }
      } finally {
        this.editCodeLoading = false
      }
    },
    copyCurrentModified() {
      if (this.editCodeSelectedFile >= 0 && this.editModifyResult[this.editCodeSelectedFile]) {
        navigator.clipboard.writeText(this.editModifyResult[this.editCodeSelectedFile].modified)
        this.$message.success('已复制修改后代码')
      }
    },
    async downloadModifiedZip() {
      try {
        const res = await axios.post('/api/generate/modify-code/download', {
          files: this.editModifyResult
        }, { responseType: 'blob' })
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a')
        a.href = url
        a.download = 'modified-project.zip'
        a.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        this.$message.error('下载失败')
      }
    },
    async analyzeCode() {
      if (!this.fixProjectPath.trim()) { this.$message.warning('请输入项目路径'); return }
      this.analyzing = true
      this.analysisResult = null
      this.selectedErrors = []
      this.repairResults = []
      try {
        const res = await axios.post('/api/fix/analyze', { path: this.fixProjectPath })
        this.analysisResult = res.data
        this.fixTempDir = res.data.temp_dir || ''
        if (res.data.total > 0) { this.$message.warning(`发现 ${res.data.total} 个问题`) }
        else { this.$message.success('未检测到问题') }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '分析失败')
      } finally { this.analyzing = false }
    },
    async analyzeRemoteCode() {
      if (!this.fixServerId) { this.$message.warning('请选择服务器'); return }
      if (!this.fixProjectPath.trim()) { this.$message.warning('请输入项目路径'); return }
      this.analyzing = true
      this.analysisResult = null
      this.selectedErrors = []
      this.repairResults = []
      this.fixTempDir = ''
      try {
        const res = await axios.post('/api/fix/analyze-remote', {
          server_id: this.fixServerId,
          project_path: this.fixProjectPath,
          user_id: this.userId,
        })
        this.analysisResult = res.data
        this.fixTempDir = res.data.temp_dir || ''
        if (res.data.total > 0) { this.$message.warning(`发现 ${res.data.total} 个问题`) }
        else { this.$message.success('未检测到问题') }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '远程检测失败')
      } finally { this.analyzing = false }
    },
    triggerFixZipSelect() { this.$refs.fixZipInput.click() },
    handleFixZipSelect(e) {
      const file = e.target.files[0]
      if (file && file.name.endsWith('.zip')) {
        if (file.size > 10 * 1024 * 1024) { this.$message.warning('文件不能超过 10MB'); return }
        this.fixUploadFile = file
      }
    },
    handleFixZipDrop(e) {
      const file = e.dataTransfer.files[0]
      if (file && file.name.endsWith('.zip')) {
        if (file.size > 10 * 1024 * 1024) { this.$message.warning('文件不能超过 10MB'); return }
        this.fixUploadFile = file
      }
    },
    async analyzeUploadedCode() {
      if (!this.fixUploadFile) { this.$message.warning('请先上传项目ZIP'); return }
      this.analyzing = true
      this.analysisResult = null
      this.selectedErrors = []
      this.repairResults = []
      this.fixTempDir = ''
      try {
        const formData = new FormData()
        formData.append('file', this.fixUploadFile)
        if (this.userId) formData.append('user_id', this.userId)
        const res = await axios.post('/api/fix/analyze-upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.analysisResult = res.data
        this.fixTempDir = res.data.temp_dir || ''
        if (res.data.total > 0) { this.$message.warning(`发现 ${res.data.total} 个问题`) }
        else { this.$message.success('未检测到问题') }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '分析失败')
      } finally { this.analyzing = false }
    },
    async repairErrorsNew() {
      if (this.selectedErrors.length === 0) return
      if (!(await this.requireCredits(200, '代码修复'))) return
      this.repairing = true
      this.repairResults = []
      try {
        const errors = this.selectedErrors.map(idx => this.analysisResult.errors[idx])
        let res
        if (this.fixMode === 'upload') {
          res = await axios.post('/api/fix/repair-upload', {
            temp_dir: this.fixTempDir,
            errors: errors,
            user_id: this.userId,
          })
        } else {
          res = await axios.post('/api/fix/repair-remote', {
            server_id: this.fixServerId,
            project_path: this.fixProjectPath,
            errors: errors,
            user_id: this.userId,
          })
        }
        this.repairResults = res.data.results.map(r => ({ ...r, applied: false }))
        this.updateCreditsFromResponse(res)
        this.$message.success(`AI 修复完成，共 ${this.repairResults.length} 个文件，消耗 200 积分`)
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '修复失败')
        }
      } finally { this.repairing = false }
    },
    async downloadRepairedZip() {
      if (!this.fixTempDir) { this.$message.warning('无可下载的内容'); return }
      try {
        const res = await axios.post('/api/fix/download-repaired', {
          temp_dir: this.fixTempDir,
        }, { responseType: 'blob' })
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a')
        a.href = url
        a.download = 'repaired-project.zip'
        a.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        this.$message.error('下载失败')
      }
    },
    openSaveToServer() {
      if (this.servers.length === 0) {
        this.$message.warning('暂无已配置的服务器，请先去「免费部署」tab配置')
        return
      }
      this.saveServerId = '0'
      this.saveTargetPath = '/www/wwwroot/my-project/'
      this.saveToServerVisible = true
    },
    async doSaveToServer() {
      if (!this.saveServerId) { this.$message.warning('请选择服务器'); return }
      if (!this.saveTargetPath.trim()) { this.$message.warning('请输入目标路径'); return }
      this.saveToServerLoading = true
      try {
        const res = await axios.post('/api/generate/save-to-server', {
          files: this.genFiles,
          server_id: this.saveServerId,
          target_path: this.saveTargetPath.trim(),
          user_id: this.userId,
        })
        this.$message.success(res.data.message || '保存成功')
        this.saveToServerVisible = false
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '保存失败')
      } finally {
        this.saveToServerLoading = false
      }
    },
    toggleError(idx) {
      const pos = this.selectedErrors.indexOf(idx)
      if (pos === -1) this.selectedErrors.push(idx)
      else this.selectedErrors.splice(pos, 1)
    },
    selectAllErrors() {
      if (!this.analysisResult) return
      this.selectedErrors = this.analysisResult.errors.map((_, i) => i)
    },
    async repairErrors() {
      if (this.selectedErrors.length === 0) return
      if (!(await this.requireCredits(200, '代码修复'))) return
      this.repairing = true
      this.repairResults = []
      try {
        const errors = this.selectedErrors.map(idx => this.analysisResult.errors[idx])
        const res = await axios.post('/api/fix/repair', { path: this.fixProjectPath, errors })
        this.repairResults = res.data.results.map(r => ({ ...r, applied: false }))
        this.updateCreditsFromResponse(res)
        this.$message.success(`AI 修复完成，共 ${this.repairResults.length} 个文件，消耗 200 积分`)
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '修复失败')
        }
      } finally { this.repairing = false }
    },
    async applyFix(result) {
      try {
        await axios.post('/api/fix/apply', { path: this.fixProjectPath, fixes: [{ file: result.file, fixed: result.fixed }] })
        result.applied = true
        this.$message.success(`${result.file} 修复已应用`)
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '应用修复失败')
      }
    },
    errorTypeLabel(type) {
      return { syntax: '语法', import: '依赖', type: '类型', config: '配置', bracket: '括号' }[type] || type
    },

    // ===== User Profile =====
    async loadUserProfile() {
      if (!this.isLoggedIn) return
      try {
        const res = await axios.get('/api/auth/profile', {
          headers: { 'x-user-id': this.userId },
        })
        this.userProfile = res.data
        this.userCredits = res.data.credits || 0
        this.userProfileLoaded = true
      } catch { /* ignore */ }
    },
    formatFullTime(t) {
      if (!t) return '-'
      try {
        return new Date(t).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
      } catch { return t }
    },


    // ===== Credits =====
    formatCredits(val) {
      if (val === undefined || val === null) return '0'
      return val.toLocaleString()
    },
    async loadCreditLogs() {
      try {
        const params = this.adminCreditUserId ? `?user_id=${this.adminCreditUserId}` : ''
        const res = await axios.get(`/api/admin/credit-logs${params}`, { headers: this.getAdminHeaders() })
        this.creditLogs = res.data.logs || []
      } catch (err) {
        if (err.response?.status === 403) this.$message.error('需要管理员权限')
      }
    },
    async adminAddCredits() {
      if (!this.adminAddCreditUserId.trim()) { this.$message.warning('请输入用户ID'); return }
      if (!this.adminAddCreditAmount || this.adminAddCreditAmount <= 0) { this.$message.warning('积分数量必须大于0'); return }
      this.adminAddCreditLoading = true
      try {
        const res = await axios.post('/api/admin/add-credits', {
          user_id: this.adminAddCreditUserId.trim(),
          amount: this.adminAddCreditAmount,
          description: this.adminAddCreditDesc || '管理员手动充值',
        }, { headers: this.getAdminHeaders() })
        this.$message.success(res.data.message || '积分添加成功')
        this.adminAddCreditUserId = ''
        this.adminAddCreditAmount = 1000
        this.adminAddCreditDesc = ''
        await this.loadCreditLogs()
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '添加积分失败')
      } finally {
        this.adminAddCreditLoading = false
      }
    },
    updateCreditsFromResponse(res) {
      if (res.data && res.data.credits_remaining !== undefined && res.data.credits_remaining !== null) {
        this.userCredits = res.data.credits_remaining
      }
    },

    // ===== Edit Code Tab =====
    async analyzeCode() {
      if (!this.fixProjectPath.trim()) { this.$message.warning('请输入项目路径'); return }
      this.analyzing = true
      this.analysisResult = null
      this.selectedErrors = []
      this.repairResults = []
      try {
        const res = await axios.post('/api/fix/analyze', { path: this.fixProjectPath })
        this.analysisResult = res.data
        this.fixTempDir = res.data.temp_dir || ''
        if (res.data.total > 0) { this.$message.warning(`发现 ${res.data.total} 个问题`) }
        else { this.$message.success('未检测到问题') }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '分析失败')
      } finally { this.analyzing = false }
    },
    async analyzeRemoteCode() {
      if (!this.fixServerId) { this.$message.warning('请选择服务器'); return }
      if (!this.fixProjectPath.trim()) { this.$message.warning('请输入项目路径'); return }
      this.analyzing = true
      this.analysisResult = null
      this.selectedErrors = []
      this.repairResults = []
      this.fixTempDir = ''
      try {
        const res = await axios.post('/api/fix/analyze-remote', {
          server_id: this.fixServerId,
          project_path: this.fixProjectPath,
          user_id: this.userId,
        })
        this.analysisResult = res.data
        this.fixTempDir = res.data.temp_dir || ''
        if (res.data.total > 0) { this.$message.warning(`发现 ${res.data.total} 个问题`) }
        else { this.$message.success('未检测到问题') }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '远程检测失败')
      } finally { this.analyzing = false }
    },
    triggerFixZipSelect() { this.$refs.fixZipInput.click() },
    handleFixZipSelect(e) {
      const file = e.target.files[0]
      if (file && file.name.endsWith('.zip')) {
        if (file.size > 10 * 1024 * 1024) { this.$message.warning('文件不能超过 10MB'); return }
        this.fixUploadFile = file
      }
    },
    handleFixZipDrop(e) {
      const file = e.dataTransfer.files[0]
      if (file && file.name.endsWith('.zip')) {
        if (file.size > 10 * 1024 * 1024) { this.$message.warning('文件不能超过 10MB'); return }
        this.fixUploadFile = file
      }
    },
    async analyzeUploadedCode() {
      if (!this.fixUploadFile) { this.$message.warning('请先上传项目ZIP'); return }
      this.analyzing = true
      this.analysisResult = null
      this.selectedErrors = []
      this.repairResults = []
      this.fixTempDir = ''
      try {
        const formData = new FormData()
        formData.append('file', this.fixUploadFile)
        if (this.userId) formData.append('user_id', this.userId)
        const res = await axios.post('/api/fix/analyze-upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.analysisResult = res.data
        this.fixTempDir = res.data.temp_dir || ''
        if (res.data.total > 0) { this.$message.warning(`发现 ${res.data.total} 个问题`) }
        else { this.$message.success('未检测到问题') }
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '分析失败')
      } finally { this.analyzing = false }
    },
    async repairErrorsNew() {
      if (this.selectedErrors.length === 0) return
      if (!(await this.requireCredits(200, '代码修复'))) return
      this.repairing = true
      this.repairResults = []
      try {
        const errors = this.selectedErrors.map(idx => this.analysisResult.errors[idx])
        let res
        if (this.fixMode === 'upload') {
          res = await axios.post('/api/fix/repair-upload', {
            temp_dir: this.fixTempDir,
            errors: errors,
            user_id: this.userId,
          })
        } else {
          res = await axios.post('/api/fix/repair-remote', {
            server_id: this.fixServerId,
            project_path: this.fixProjectPath,
            errors: errors,
            user_id: this.userId,
          })
        }
        this.repairResults = res.data.results.map(r => ({ ...r, applied: false }))
        this.updateCreditsFromResponse(res)
        this.$message.success(`AI 修复完成，共 ${this.repairResults.length} 个文件，消耗 200 积分`)
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '修复失败')
        }
      } finally { this.repairing = false }
    },
    async downloadRepairedZip() {
      if (!this.fixTempDir) { this.$message.warning('无可下载的内容'); return }
      try {
        const res = await axios.post('/api/fix/download-repaired', {
          temp_dir: this.fixTempDir,
        }, { responseType: 'blob' })
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a')
        a.href = url
        a.download = 'repaired-project.zip'
        a.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        this.$message.error('下载失败')
      }
    },
    openSaveToServer() {
      if (this.servers.length === 0) {
        this.$message.warning('暂无已配置的服务器，请先去「免费部署」tab配置')
        return
      }
      this.saveServerId = '0'
      this.saveTargetPath = '/www/wwwroot/my-project/'
      this.saveToServerVisible = true
    },
    async doSaveToServer() {
      if (!this.saveServerId) { this.$message.warning('请选择服务器'); return }
      if (!this.saveTargetPath.trim()) { this.$message.warning('请输入目标路径'); return }
      this.saveToServerLoading = true
      try {
        const res = await axios.post('/api/generate/save-to-server', {
          files: this.genFiles,
          server_id: this.saveServerId,
          target_path: this.saveTargetPath.trim(),
          user_id: this.userId,
        })
        this.$message.success(res.data.message || '保存成功')
        this.saveToServerVisible = false
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '保存失败')
      } finally {
        this.saveToServerLoading = false
      }
    },
    toggleError(idx) {
      const pos = this.selectedErrors.indexOf(idx)
      if (pos === -1) this.selectedErrors.push(idx)
      else this.selectedErrors.splice(pos, 1)
    },
    selectAllErrors() {
      if (!this.analysisResult) return
      this.selectedErrors = this.analysisResult.errors.map((_, i) => i)
    },
    async repairErrors() {
      if (this.selectedErrors.length === 0) return
      if (!(await this.requireCredits(200, '代码修复'))) return
      this.repairing = true
      this.repairResults = []
      try {
        const errors = this.selectedErrors.map(idx => this.analysisResult.errors[idx])
        const res = await axios.post('/api/fix/repair', { path: this.fixProjectPath, errors })
        this.repairResults = res.data.results.map(r => ({ ...r, applied: false }))
        this.updateCreditsFromResponse(res)
        this.$message.success(`AI 修复完成，共 ${this.repairResults.length} 个文件，消耗 200 积分`)
      } catch (err) {
        if (err.response?.status === 402) {
          this.showPaymentDialog()
        } else {
          this.$message.error(err.response?.data?.detail || '修复失败')
        }
      } finally { this.repairing = false }
    },
    async applyFix(result) {
      try {
        await axios.post('/api/fix/apply', { path: this.fixProjectPath, fixes: [{ file: result.file, fixed: result.fixed }] })
        result.applied = true
        this.$message.success(`${result.file} 修复已应用`)
      } catch (err) {
        this.$message.error(err.response?.data?.detail || '应用修复失败')
      }
    },
    errorTypeLabel(type) {
      return { syntax: '语法', import: '依赖', type: '类型', config: '配置', bracket: '括号' }[type] || type
    },

    // ===== User Profile =====
    async loadUserProfile() {
      if (!this.isLoggedIn) return
      try {
        const res = await axios.get('/api/auth/profile', {
          headers: { 'x-user-id': this.userId },
        })
        this.userProfile = res.data
        this.userCredits = res.data.credits || 0
        this.userProfileLoaded = true
      } catch { /* ignore */ }
    },
    formatFullTime(t) {
      if (!t) return '-'
      try {
        return new Date(t).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
      } catch { return t }
    },

    // ===== Edit Code Tab =====
    copyModifiedCode() {
      if (this.editCodeResult) {
        navigator.clipboard.writeText(this.editCodeResult)
        this.$message.success('已复制修改后的代码')
      }
    },
  },
}
</script>

<style scoped>
.app-container { min-height: 100vh; display: flex; flex-direction: column; max-width: 960px; margin: 0 auto; padding: 0 24px; }

/* Header */
.app-header { display: flex; align-items: center; justify-content: space-between; padding: 24px 0; border-bottom: 1px solid var(--border-color); }
.header-left { display: flex; align-items: center; gap: 12px; cursor: default; user-select: none; }
.header-right { display: flex; align-items: center; gap: 16px; }
.logo { font-size: 28px; }
.header-left h1 { font-size: 22px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
.version { font-size: 12px; color: var(--text-secondary); background: var(--bg-tertiary); padding: 2px 8px; border-radius: 10px; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.vip-tag { cursor: pointer; transition: all 0.2s; }
.vip-tag:hover { transform: scale(1.05); }

/* Tab Bar */
.tab-bar { display: flex; gap: 4px; background: var(--bg-tertiary); border-radius: 8px; padding: 3px; }
.tab-btn { padding: 6px 16px; border: none; border-radius: 6px; background: transparent; color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; font-family: inherit; white-space: nowrap; }
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { background: var(--bg-secondary); color: var(--text-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.admin-tab { color: var(--accent-orange); }
.admin-tab.active { background: rgba(210, 153, 34, 0.15); color: var(--accent-orange); }

/* Main */
.main-content { flex: 1; padding: 24px 0; display: flex; flex-direction: column; gap: 20px; }

/* Step Section */
.step-section { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); }
.step-header { display: flex; align-items: center; gap: 12px; padding: 16px 20px; border-bottom: 1px solid var(--border-color); background: var(--bg-tertiary); flex-wrap: wrap; }
.step-num { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: var(--accent-green); color: #000; font-weight: 700; font-size: 13px; border-radius: 50%; }
.step-num.fix-num { background: var(--accent-orange); }
.step-num.gen-num { background: var(--accent-purple); color: #fff; }
.step-num.admin-num { background: var(--accent-orange); color: #fff; font-size: 16px; width: auto; border-radius: 6px; padding: 0 6px; }
.step-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.step-body { padding: 20px; }

/* Usage Guide */
.usage-guide { margin-bottom: 8px; }
.guide-header { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 16px 20px; user-select: none; }
.guide-icon { font-size: 18px; }
.guide-title { font-size: 15px; font-weight: 600; color: var(--text-primary); flex: 1; }
.guide-arrow { transition: transform 0.3s; color: var(--text-secondary); }
.guide-arrow.expanded { transform: rotate(180deg); }

.ssh-collapsible { margin-top: 20px; }
.ssh-collapse-header {
  display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; padding: 12px 16px;
  background: rgba(255,255,255,0.03); border-radius: 8px;
  font-weight: 500; color: var(--text-primary);
}
.ssh-collapse-header:hover { background: rgba(255,255,255,0.06); }
.ssh-status-connected { color: #67c23a; font-size: 13px; margin-left: auto; margin-right: 8px; }
.ssh-collapse-body { padding: 16px 0 0; }

.guide-body { padding: 0 20px 16px 20px; }
.guide-steps { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.guide-step { display: flex; gap: 12px; padding: 12px; background: var(--bg-tertiary); border-radius: 8px; border: 1px solid var(--border-color); }
.guide-step-num { width: 28px; height: 28px; border-radius: 50%; background: var(--accent-blue); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.guide-step-content { flex: 1; }
.guide-step-content h4 { font-size: 14px; color: var(--text-primary); margin: 0 0 4px 0; }
.guide-step-content p { font-size: 12px; color: var(--text-secondary); margin: 0; line-height: 1.5; }

/* Path Select Row */
.path-select-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.path-select-label { font-size: 13px; color: var(--text-secondary); white-space: nowrap; flex-shrink: 0; }

/* SSH Connection Form */
.ssh-form { display: flex; flex-direction: column; gap: 12px; }
.ssh-form-row { display: flex; gap: 12px; flex-wrap: wrap; }
.ssh-form-item { display: flex; flex-direction: column; gap: 6px; }
.ssh-form-item label { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.connected-badge { margin-left: auto; }

/* SSH Connected State */
.ssh-connected { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: rgba(63, 185, 80, 0.08); border: 1px solid rgba(63, 185, 80, 0.2); border-radius: 10px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12); }
.ssh-connected-info { display: flex; align-items: center; gap: 12px; }
.ssh-connected-icon { font-size: 24px; }
.ssh-connected-host { font-size: 15px; font-weight: 600; color: var(--accent-green); }
.ssh-connected-user { font-size: 12px; color: var(--text-secondary); font-family: monospace; }

/* Path Section */
.path-section { margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color); }

.result-summary { display: flex; gap: 8px; margin-left: auto; }
.selected-count { font-size: 13px; color: var(--accent-purple); margin-left: auto; }

/* Action Row */
.action-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; margin-top: 8px; }

/* Info Grid */
.info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.info-item { display: flex; flex-direction: column; gap: 6px; }
.info-label { font-size: 12px; color: var(--text-secondary); }
.info-value { font-size: 14px; font-weight: 500; }
.info-value.highlight { color: var(--accent-blue); }
.info-value.code { font-family: monospace; color: var(--accent-green); }
.info-value.dim { color: var(--text-secondary); }

/* Config Row */
.config-row { display: flex; gap: 16px; flex-wrap: wrap; }
.config-item { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 8px; }
.config-item label { font-size: 13px; color: var(--text-secondary); font-weight: 500; }

/* Terminal */
.terminal-container { margin-top: 20px; border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }
.terminal-header { display: flex; align-items: center; padding: 10px 16px; background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color); gap: 12px; }
.terminal-dots { display: flex; gap: 6px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.red { background: #ff5f57; } .dot.yellow { background: #febc2e; } .dot.green { background: #28c840; }
.terminal-title { flex: 1; font-size: 13px; color: var(--text-secondary); text-align: center; }
.terminal-actions { display: flex; gap: 4px; }
.terminal-body { background: var(--terminal-bg); padding: 16px; max-height: 500px; overflow: auto; }
.terminal-body.compact { max-height: 300px; }
.terminal-body pre { margin: 0; white-space: pre-wrap; word-break: break-all; font-size: 13px; line-height: 1.6; color: var(--terminal-green); font-family: 'JetBrains Mono', 'Fira Code', monospace; }

/* Remote Log */
.remote-log .terminal-body pre code { display: block; padding: 2px 0; }
.log-warn { color: var(--accent-orange) !important; }
.log-err { color: #f85149 !important; }
.log-ok { color: var(--accent-green) !important; }
.pulse-tag { animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Extra files */
.extra-files { margin-top: 16px; }
.extra-files h4 { font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; }
.extra-file-item { border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; margin-bottom: 12px; }
.extra-file-header { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: var(--bg-tertiary); font-size: 13px; color: var(--text-primary); }

/* ===== Generate Tab ===== */
.pay-hint { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; color: var(--accent-orange); margin-left: 12px; cursor: pointer; }
.pay-hint:hover { text-decoration: underline; }

.gen-file-list { display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; max-height: 200px; overflow-y: auto; }
.gen-file-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
.gen-file-item:hover { background: var(--bg-tertiary); }
.gen-file-item.active { background: var(--bg-tertiary); border-color: var(--accent-purple); }
.gen-file-icon { font-size: 14px; }
.gen-file-name { font-size: 13px; color: var(--accent-blue); font-family: monospace; }
.gen-actions { margin-top: 16px; }

/* ===== Error List ===== */
.no-errors { text-align: center; padding: 32px 0; }
.no-errors-icon { font-size: 48px; display: block; margin-bottom: 12px; }
.no-errors p { color: var(--text-secondary); font-size: 14px; }
.error-list { display: flex; flex-direction: column; gap: 8px; }
.error-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border: 1px solid var(--border-color); border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.error-item:hover { border-color: var(--text-secondary); }
.error-item.selected { border-color: var(--accent-orange); background: rgba(210, 153, 34, 0.05); }
.error-item.error { border-left: 3px solid #f85149; }
.error-item.warning { border-left: 3px solid #d29922; }
.error-left { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.error-severity { font-size: 16px; width: 24px; text-align: center; }
.error-severity.error { color: #f85149; } .error-severity.warning { color: #d29922; }
.error-type-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: var(--bg-tertiary); color: var(--text-secondary); white-space: nowrap; }
.error-center { flex: 1; min-width: 0; }
.error-file { font-size: 13px; color: var(--accent-blue); font-family: monospace; }
.error-line { font-size: 13px; color: var(--text-secondary); font-family: monospace; }
.error-msg { font-size: 12px; color: var(--text-secondary); margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.error-right { flex-shrink: 0; }

/* Fix Actions */
.fix-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; margin-top: 8px; align-items: center; }

/* Repair Results / Diff */
.repair-results { margin-top: 12px; }
.repair-results h4 { font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; }
.repair-item { border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; margin-bottom: 16px; }
.repair-file-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color); }
.repair-filename { font-size: 13px; color: var(--accent-blue); font-family: monospace; }
.diff-container { display: flex; background: var(--terminal-bg); overflow: hidden; }
.diff-side { flex: 1; min-width: 0; overflow: auto; max-height: 400px; }
.diff-label { padding: 6px 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); position: sticky; top: 0; z-index: 1; }
.diff-side:first-child .diff-label { color: #f85149; background: rgba(248, 81, 73, 0.08); }
.diff-side:last-child .diff-label { color: #3fb950; background: rgba(63, 185, 80, 0.08); }
.diff-code { margin: 0; padding: 12px; font-size: 12px; line-height: 1.6; font-family: 'JetBrains Mono', 'Fira Code', monospace; white-space: pre; color: var(--text-primary); }
.diff-divider { width: 1px; background: var(--border-color); flex-shrink: 0; }

/* ===== Credit Cost Hint ===== */
.credit-cost-hint { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; color: var(--accent-orange); margin-left: 12px; font-weight: 500; }
.free-badge { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; color: var(--accent-green); margin-left: 12px; font-weight: 600; background: rgba(63, 185, 80, 0.1); padding: 4px 12px; border-radius: 14px; border: 1px solid rgba(63, 185, 80, 0.3); }
.credits-badge-small { font-size: 10px; cursor: pointer; }
.plan-credits { font-size: 13px; color: var(--accent-blue); font-weight: 600; margin-bottom: 4px; }

/* ===== Payment Dialog ===== */
.payment-content { padding: 0 4px; }
.payment-plans { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.credit-packages .plan-card { flex: 1; min-width: 120px; padding: 16px 12px; }
.plan-card { flex: 1; border: 2px solid var(--border-color); border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.3s; position: relative; }
.plan-card:hover { border-color: var(--text-secondary); }
.plan-card.selected { border-color: var(--accent-blue); background: rgba(88, 166, 255, 0.05); }
.plan-card.recommend { border-color: var(--accent-blue); }
.plan-badge { position: absolute; top: -1px; right: 16px; background: var(--accent-blue); color: #fff; font-size: 11px; padding: 2px 10px; border-radius: 0 0 8px 8px; font-weight: 600; }
.plan-name { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; }
.plan-price { margin-bottom: 8px; }
.price-symbol { font-size: 16px; color: var(--accent-orange); font-weight: 600; }
.price-num { font-size: 36px; font-weight: 700; color: var(--accent-orange); }
.plan-desc { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.plan-unit { font-size: 12px; color: var(--text-secondary); }
.payment-features { padding: 16px; background: var(--bg-tertiary); border-radius: 8px; }
.feature-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 14px; color: var(--text-primary); }
.feat-check { color: var(--accent-green); font-weight: 700; }
.payment-footer { text-align: center; }

/* ===== Admin Styles ===== */
.admin-subtabs { display: flex; gap: 4px; background: var(--bg-tertiary); border-radius: 8px; padding: 3px; flex-wrap: wrap; }
.subtab-btn { padding: 8px 16px; border: none; border-radius: 6px; background: transparent; color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.subtab-btn:hover { color: var(--text-primary); }
.subtab-btn.active { background: rgba(210, 153, 34, 0.15); color: var(--accent-orange); box-shadow: 0 1px 3px rgba(0,0,0,0.2); }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; background: var(--bg-tertiary); border-radius: 12px; border: 1px solid var(--border-color); transition: transform 0.2s; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25); }
.stat-card.accent-orange { border-color: var(--accent-orange); }
.stat-card.accent-blue { border-color: var(--accent-blue); }
.stat-card.accent-green { border-color: var(--accent-green); }
.stat-icon { font-size: 32px; }
.stat-info { flex: 1; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

/* Admin Table */
.admin-table-wrapper { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { text-align: left; padding: 10px 12px; background: var(--bg-tertiary); color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid var(--border-color); color: var(--text-primary); }
.admin-table tr:hover td { background: rgba(255,255,255,0.02); }
.user-id-cell { font-family: monospace; font-size: 12px; color: var(--accent-blue); max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.time-cell { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
.amount-cell { font-weight: 600; color: var(--accent-orange); }
.msg-cell { font-size: 12px; color: var(--text-secondary); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dim { color: var(--text-secondary); }

/* Config Section */
.config-section { margin-bottom: 24px; }
.config-section h4 { font-size: 15px; color: var(--text-primary); margin-bottom: 12px; font-weight: 600; }
.config-form { display: flex; gap: 24px; flex-wrap: wrap; }
.config-form-item { display: flex; flex-direction: column; gap: 6px; }
.config-form-item label { font-size: 13px; color: var(--text-secondary); }
.config-hint { font-size: 12px; color: var(--text-secondary); margin-top: 8px; }
.config-hint code { background: var(--bg-tertiary); padding: 2px 6px; border-radius: 4px; font-size: 11px; }

.empty-state { text-align: center; padding: 40px 0; color: var(--text-secondary); }
.empty-state span { font-size: 48px; display: block; margin-bottom: 12px; }

.admin-login-content { padding: 8px 0; }

/* Login Dialog */
.login-content { padding: 8px 0; }
.login-actions { margin-top: 16px; }
.login-switch { text-align: center; margin-top: 16px; font-size: 14px; color: var(--text-secondary); }

/* Footer */
.app-footer { padding: 20px 0; text-align: center; font-size: 12px; color: var(--text-secondary); border-top: 1px solid var(--border-color); }
.separator { margin: 0 8px; }

/* Animations */
.fade-in { animation: fadeIn 0.3s ease-in; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* ===== User Profile Popover ===== */
.user-tag-wrapper { display: flex; align-items: center; gap: 4px; cursor: pointer; padding: 4px 8px; border-radius: 20px; transition: background 0.2s; }
.user-tag-wrapper:hover { background: var(--bg-tertiary); }
.user-tag-clickable { cursor: pointer; }
.vip-badge-small { font-size: 10px; }
.profile-popover { padding: 4px 0; }
.profile-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--bg-tertiary); border-radius: 8px; margin-bottom: 12px; }
.profile-avatar { width: 42px; height: 42px; border-radius: 50%; background: var(--accent-blue); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; flex-shrink: 0; }
.profile-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.profile-info { display: flex; flex-direction: column; gap: 10px; padding: 0 4px; }
.profile-row { display: flex; align-items: center; justify-content: space-between; font-size: 13px; }
.profile-label { color: var(--text-secondary); }
.profile-value { color: var(--text-primary); font-weight: 500; }
.profile-value.mono { font-family: monospace; font-size: 11px; color: var(--text-secondary); }
.text-expired { color: #f85149 !important; }
.profile-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border-color); }

/* ===== Edit Code Tab ===== */
.step-num.edit-num { background: #8b5cf6; color: #fff; }
.editcode-tips { padding: 20px; }
.upload-zone { border: 2px dashed var(--border-color); border-radius: 12px; padding: 40px 20px; text-align: center; cursor: pointer; transition: all 0.3s; background: var(--bg-primary); }
.upload-zone:hover { border-color: var(--accent-purple); background: rgba(188, 140, 255, 0.03); }
.upload-icon { font-size: 48px; margin-bottom: 12px; }
.upload-text { font-size: 14px; color: var(--text-primary); margin-bottom: 8px; }
.upload-text em { color: var(--accent-blue); font-style: normal; }
.upload-hint { font-size: 12px; color: var(--text-secondary); }
.file-info-bar { margin-top: 12px; font-size: 13px; color: var(--accent-blue); padding: 8px 14px; background: var(--bg-tertiary); border-radius: 8px; display: flex; align-items: center; }
.editcode-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; align-items: center; margin-top: 8px; }
.editcode-tips-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; }
.editcode-tips-list { list-style: none; padding: 0; margin: 0 0 12px 0; display: flex; flex-direction: column; gap: 6px; }
.editcode-tips-list li { font-size: 13px; color: var(--text-secondary); padding-left: 20px; position: relative; line-height: 1.6; }
.editcode-tips-list li::before { content: '✓'; position: absolute; left: 0; color: var(--accent-green); font-weight: 700; }
.editcode-tips-warn { font-size: 13px; color: var(--accent-blue); padding: 10px 14px; background: rgba(88, 166, 255, 0.08); border: 1px solid rgba(88, 166, 255, 0.2); border-radius: 8px; margin-top: 8px; }
.editcode-form { display: flex; flex-direction: column; gap: 12px; }
.editcode-editor :deep(textarea) { font-family: 'JetBrains Mono', 'Fira Code', monospace !important; font-size: 13px !important; line-height: 1.6 !important; background: var(--terminal-bg) !important; color: var(--terminal-green) !important; border: 1px solid var(--border-color) !important; border-radius: 8px !important; padding: 16px !important; }
.editcode-actions { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }

/* Fix Mode Tabs */
.fix-mode-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.fix-mode-card { border: 2px solid var(--border-color); border-radius: 12px; padding: 24px 16px; text-align: center; cursor: pointer; transition: all 0.3s; background: var(--bg-tertiary); }
.fix-mode-card:hover { border-color: var(--accent-orange); background: rgba(210, 153, 34, 0.04); }
.fix-mode-card.active { border-color: var(--accent-orange); background: rgba(210, 153, 34, 0.08); box-shadow: 0 0 16px rgba(210, 153, 34, 0.15); }
.fix-mode-icon { font-size: 36px; margin-bottom: 8px; }
.fix-mode-label { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.fix-mode-desc { font-size: 12px; color: var(--text-secondary); }

/* Responsive */
@media (max-width: 600px) {
  .app-container { padding: 0 12px; }
  .info-grid { grid-template-columns: 1fr; }
  .config-row { flex-direction: column; }
  .diff-container { flex-direction: column; }
  .diff-divider { width: auto; height: 1px; }
  .header-right { flex-direction: column; align-items: flex-end; gap: 8px; }
  .payment-plans { flex-direction: column; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .fix-mode-tabs { grid-template-columns: 1fr; }
}

/* PWA Install Button */
.pwa-install-btn {
  padding: 4px 12px;
  border: 1px solid var(--accent-blue);
  border-radius: 14px;
  background: rgba(88, 166, 255, 0.1);
  color: var(--accent-blue);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  font-family: inherit;
}
.pwa-install-btn:hover {
  background: rgba(88, 166, 255, 0.2);
}


/* ===== Skills Tab (配置生成) ===== */
.skills-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.skill-card { 
  border: 2px solid var(--border-color); 
  border-radius: 12px; 
  padding: 20px 16px; 
  text-align: center; 
  cursor: pointer; 
  transition: all 0.3s; 
  background: var(--bg-tertiary); 
}
.skill-card:hover { border-color: var(--accent-blue); background: rgba(88, 166, 255, 0.04); transform: translateY(-2px); }
.skill-card.active { border-color: var(--accent-green); background: rgba(63, 185, 80, 0.08); box-shadow: 0 0 16px rgba(63, 185, 80, 0.15); }
.skill-card-icon { font-size: 32px; margin-bottom: 8px; }
.skill-card-name { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.skill-card-desc { font-size: 11px; color: var(--text-secondary); line-height: 1.4; }
.skill-input-area { margin-top: 8px; }
.skill-input-area :deep(textarea) { 
  font-family: inherit !important; 
  background: var(--bg-secondary) !important; 
  color: var(--text-primary) !important; 
  border: 1px solid var(--border-color) !important; 
  border-radius: 8px !important; 
}
.skill-result-area { position: relative; }
.result-actions { display: flex; gap: 8px; margin-bottom: 12px; }
.skill-result-code { 
  background: var(--terminal-bg); 
  color: var(--terminal-green); 
  padding: 16px; 
  border-radius: 8px; 
  font-family: 'JetBrains Mono', 'Fira Code', monospace; 
  font-size: 13px; 
  line-height: 1.6; 
  white-space: pre-wrap; 
  word-break: break-all; 
  max-height: 500px; 
  overflow-y: auto; 
  border: 1px solid var(--border-color); 
}

@media (max-width: 1200px) { .skills-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .skills-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .skills-grid { grid-template-columns: 1fr; } }


/* ===== 项目中心 ===== */
.projects-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.project-stat-card { background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px; text-align: center; }
.project-stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.project-stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.projects-list { display: grid; gap: 12px; }
.project-item { background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px; transition: all 0.2s; }
.project-item:hover { border-color: var(--accent-blue); transform: translateY(-1px); }
.project-item-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.project-item-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.project-item-status { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
.project-item-status.running { color: var(--accent-green); background: rgba(63, 185, 80, 0.1); border: 1px solid rgba(63, 185, 80, 0.3); }
.project-item-status.stopped { color: var(--text-secondary); background: var(--bg-secondary); }
.project-item-info { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.project-item-desc { font-size: 12px; color: var(--text-secondary); }
@media (max-width: 600px) { .projects-stats { grid-template-columns: repeat(2, 1fr); } }

</style>
