# Theme System Guide

## Overview

This project uses a **fully scalable CSS variable-based theme system** that requires **zero manual CSS changes** when switching between light and dark modes.

## How It Works

### 1. CSS Variables (index.css)

All colors are defined as CSS variables in HSL format:

```css
:root {
  --background: 36 20% 97%;
  --foreground: 0 0% 7%;
  /* ... more variables */
}

.dark {
  --background: 0 0% 9%;
  --foreground: 0 0% 98%;
  /* ... dark mode overrides */
}
```

**Why HSL?** HSL (Hue, Saturation, Lightness) format allows Tailwind to use opacity modifiers like `bg-background/50` for 50% opacity.

### 2. Tailwind Integration

Tailwind is configured to use these CSS variables:

```javascript
// tailwind.config.js
colors: {
  background: "hsl(var(--background))",
  foreground: "hsl(var(--foreground))",
  // ...
}
```

This means **every** Tailwind class like `bg-background`, `text-foreground`, `border-border` automatically adapts to the current theme!

### 3. Theme Provider

The `ThemeProvider` component manages theme state and applies the `.dark` class to the document root:

```tsx
<ThemeProvider defaultTheme="system" storageKey="investment-research-theme">
  <App />
</ThemeProvider>
```

Features:
- ✅ Persistent theme storage (localStorage)
- ✅ System preference detection
- ✅ Live updates on system preference change
- ✅ Smooth transitions

### 4. Theme Toggle

The `ThemeToggle` component provides a user-friendly dropdown with three options:
- **Light**: Always light mode
- **Dark**: Always dark mode
- **System**: Follow system preference (default)

## Usage

### In Components

Just use Tailwind's semantic color classes:

```tsx
// These automatically adapt to the current theme!
<div className="bg-background text-foreground">
  <Card className="bg-card text-card-foreground">
    <Button className="bg-primary text-primary-foreground">
      Click me
    </Button>
  </Card>
</div>
```

### Accessing Theme in Code

```tsx
import { useTheme } from '@/components/ThemeProvider';

function MyComponent() {
  const { theme, setTheme, actualTheme } = useTheme();
  
  // theme: 'light' | 'dark' | 'system' (user preference)
  // actualTheme: 'light' | 'dark' (resolved theme being applied)
  // setTheme: function to change theme
}
```

## Adding New Colors

To add a new color that supports both themes:

1. **Add CSS variables** to `frontend/src/index.css`:

```css
:root {
  --my-new-color: 200 100% 50%; /* Light mode */
}

.dark {
  --my-new-color: 200 80% 40%; /* Dark mode */
}
```

2. **Add to Tailwind config** in `frontend/tailwind.config.js`:

```javascript
colors: {
  "my-new": "hsl(var(--my-new-color))",
}
```

3. **Use in components**:

```tsx
<div className="bg-my-new text-my-new">
  Automatically theme-aware!
</div>
```

## Benefits

✅ **Zero Manual Changes**: Switch themes by just toggling the `.dark` class
✅ **Fully Scalable**: Add new colors once, works in both themes
✅ **Type Safe**: Full TypeScript support
✅ **Persistent**: Theme preference saved to localStorage
✅ **System Aware**: Respects user's OS preference
✅ **Smooth Transitions**: CSS transitions for color changes
✅ **Opacity Support**: Use opacity modifiers like `bg-background/50`

## Color Palette

### Light Mode (Cursor-inspired)
- Background: Warm cream/beige
- Foreground: Deep black
- Accent: Subtle muted tones

### Dark Mode (Cursor-inspired)
- Background: Dark charcoal
- Foreground: Bright white
- Accent: Slightly lighter grays

Both palettes maintain the professional, minimalist aesthetic of the Cursor website!
