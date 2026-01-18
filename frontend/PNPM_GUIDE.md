# pnpm Quick Reference Guide

This project uses **pnpm** as the package manager for improved performance and disk space efficiency.

## Installation

If you don't have pnpm installed:

```bash
# Using npm (recommended)
npm install -g pnpm

# Using PowerShell (Windows)
iwr https://get.pnpm.io/install.ps1 -useb | iex

# Using Homebrew (macOS)
brew install pnpm

# Using Chocolatey (Windows)
choco install pnpm
```

Verify installation:
```bash
pnpm --version
```

## Common Commands

| npm command | pnpm equivalent | Description |
|------------|-----------------|-------------|
| `npm install` | `pnpm install` | Install dependencies |
| `npm install <pkg>` | `pnpm add <pkg>` | Add a package |
| `npm install -D <pkg>` | `pnpm add -D <pkg>` | Add dev dependency |
| `npm uninstall <pkg>` | `pnpm remove <pkg>` | Remove a package |
| `npm update` | `pnpm update` | Update dependencies |
| `npm run <script>` | `pnpm <script>` | Run a script (shorthand) |
| `npm run dev` | `pnpm dev` | Run dev server |
| `npm run build` | `pnpm build` | Build for production |

## Getting Started

1. **Install dependencies** (first time setup):
```bash
cd frontend
pnpm install
```

2. **Run development server**:
```bash
pnpm dev
```

3. **Build for production**:
```bash
pnpm build
```

4. **Preview production build**:
```bash
pnpm preview
```

5. **Run linter**:
```bash
pnpm lint
```

6. **Format code**:
```bash
pnpm format
```

## Configuration Files

- **`.npmrc`** - pnpm configuration settings
- **`pnpm-lock.yaml`** - Lock file (similar to package-lock.json)
- **`../pnpm-workspace.yaml`** - Workspace configuration (root level)

## Key Benefits

✅ **Faster installs** - Up to 2x faster than npm  
✅ **Disk space efficient** - Shared package cache across projects  
✅ **Strict dependency resolution** - Prevents phantom dependencies  
✅ **Better monorepo support** - Built-in workspace support  
✅ **Drop-in replacement** - Same commands, better performance  

## Troubleshooting

### Peer dependency warnings
If you see peer dependency warnings, they're usually safe to ignore. The `.npmrc` file is configured to handle these automatically.

### Clear cache
If you encounter issues:
```bash
pnpm store prune
```

### Reinstall everything
```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Shamefully hoist (if needed for some packages)
If a package doesn't work due to strict node_modules structure:
```bash
# Edit .npmrc and change:
shamefully-hoist=true
# Then reinstall
pnpm install
```

## Migration from npm/yarn

Since this project didn't have a lock file yet, no migration was needed! Just:

1. Delete `node_modules` if it exists
2. Run `pnpm install`
3. Commit `pnpm-lock.yaml`

## Resources

- [pnpm Documentation](https://pnpm.io/)
- [pnpm vs npm](https://pnpm.io/feature-comparison)
- [pnpm CLI](https://pnpm.io/cli/add)
- [Workspaces](https://pnpm.io/workspaces)
