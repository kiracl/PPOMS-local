# PPOMS Web系统 - 项目脚手架 (Scaffolding)

本文件提供了快速初始化项目目录结构的脚本。

## 1. 目录结构预览
```
ppoms-web/
├── ppoms-backend/  (Spring Boot)
└── ppoms-frontend/ (Vue 3)
```

## 2. Windows 初始化脚本 (init_project.ps1)

请在项目根目录下创建一个 `init_project.ps1` 文件，并粘贴以下内容：

```powershell
# 设置编码
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 开始初始化 PPOMS Web 项目结构..." -ForegroundColor Green

# 1. 创建根目录
$root = "ppoms-web"
if (!(Test-Path $root)) { New-Item -ItemType Directory -Path $root | Out-Null }
Set-Location $root

# 2. 创建后端目录结构 (模拟 Maven 标准结构)
Write-Host "📂 创建后端目录 (ppoms-backend)..." -ForegroundColor Cyan
$backend = "ppoms-backend"
$pkgPath = "$backend/src/main/java/com/ppoms"
$resPath = "$backend/src/main/resources"

# 创建基础目录
$dirs = @(
    "$pkgPath/common",
    "$pkgPath/config",
    "$pkgPath/controller",
    "$pkgPath/entity",
    "$pkgPath/mapper",
    "$pkgPath/service/impl",
    "$pkgPath/utils",
    "$pkgPath/exception",
    "$resPath/mapper"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# 创建空白配置文件
New-Item -ItemType File -Path "$resPath/application.yml" -Force | Out-Null
New-Item -ItemType File -Path "$resPath/application-dev.yml" -Force | Out-Null
New-Item -ItemType File -Path "$backend/pom.xml" -Force | Out-Null

# 3. 创建前端目录结构
Write-Host "📂 创建前端目录 (ppoms-frontend)..." -ForegroundColor Cyan
$frontend = "ppoms-frontend"
$srcPath = "$frontend/src"

$frontDirs = @(
    "$srcPath/api",
    "$srcPath/assets/styles",
    "$srcPath/components",
    "$srcPath/layout",
    "$srcPath/router",
    "$srcPath/store",
    "$srcPath/utils",
    "$srcPath/views/login",
    "$srcPath/views/system",
    "$srcPath/views/purchase",
    "$srcPath/types"
)

foreach ($dir in $frontDirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# 创建基础文件占位符
New-Item -ItemType File -Path "$srcPath/App.vue" -Force | Out-Null
New-Item -ItemType File -Path "$srcPath/main.ts" -Force | Out-Null
New-Item -ItemType File -Path "$frontend/package.json" -Force | Out-Null
New-Item -ItemType File -Path "$frontend/vite.config.ts" -Force | Out-Null

Write-Host "✅ 项目骨架初始化完成！" -ForegroundColor Green
Write-Host "位置: $(Get-Location)"
```

## 3. 使用方法
1. 打开 PowerShell。
2. 运行 `.\init_project.ps1`。
3. 它将创建 `ppoms-web` 文件夹及其子结构。

---

## 4. 后续步骤
初始化完成后，你需要：
1. **后端**: 使用 IntelliJ IDEA 打开 `ppoms-backend`，并完善 `pom.xml`。
2. **前端**: 在 `ppoms-frontend` 下运行 `npm install` (需先填充 `package.json`)。
