# VPS Manager - UI Preview

## Main Menu
```
╔════════════════════════════════════════════════════════════╗
║                    VPS Manager                             ║
║            Connected to: 23.29.114.83:22                   ║
╚════════════════════════════════════════════════════════════╝


  Option  Description
  
  1       Live Monitoring Dashboard
  2       Provision New Site
  3       Take Site Offline (Park)
  4       Remove Site Provisioning
  5       Restart Service
  6       Restart All Services
  q       Quit


Select an option: _
```

## Live Monitoring Dashboard
```
╭─────────────────────────────────────────────────────────────────────────────╮
│                 VPS Manager - 23.29.114.83:22                                │
╰─────────────────────────────────────────────────────────────────────────────╯
┌─────────────────────────────┬─────────────────────────────────────────────┐
│                             │                                             │
│      System Status          │               Sites                         │
│                             │                                             │
│  Metric       Value         │  Domain           HTTPS  SSL      PM2       │
│  ─────────────────────      │  ───────────────────────────────────────   │
│  CPU          ████████░░ 80%│  topengineer.us    ✓    🟢 89d   🟢      │
│  Memory       ██████░░░░ 60%│  example.com       ✓    🟡 25d   🟢      │
│  Disk         ███░░░░░░░ 30%│  test.dev          ✗    🔴 3d    🔴      │
│                             │                                             │
│  NGINX        🟢 Running    │                                             │
│  PostgreSQL   🟢 Running    │                                             │
│  PM2          🟢 3/3 online │                                             │
│                             │                                             │
└─────────────────────────────┴─────────────────────────────────────────────┘
╭─────────────────────────────────────────────────────────────────────────────╮
│         Press Ctrl+C to return to menu | Updates every 5 seconds            │
╰─────────────────────────────────────────────────────────────────────────────╯
```

## Provisioning Progress
```
Provisioning example.com...

⠋ Creating directory structure...                                      [Done]
⠋ Creating Coming Soon page...                                         [Done]
⠋ Configuring NGINX...                                                 [Done]
⠋ Testing NGINX configuration...                                       [Done]
⠋ Reloading NGINX...                                                   [Done]
⠋ Obtaining SSL certificate (this may take a moment)...                [Done]

✓ Successfully provisioned example.com!
  Coming Soon page is now live at https://example.com
```

## Service Restart
```
Restarting nginx...

✓ nginx restarted successfully
```

## Site Removal Confirmation
```
⚠ Are you sure you want to completely remove example.com? (y/n): y

Removing example.com...

⠋ Stopping PM2 process...                                              [Done]
⠋ Removing NGINX configuration...                                      [Done]
⠋ Removing SSL certificate...                                          [Done]
⚠ Remove application directory /home/deployer/apps/example.com? (y/n): y
⠋ Removing application files...                                        [Done]

✓ example.com has been completely removed
```

## Color Coding Key

### Status Indicators
- 🟢 Green  = Healthy / Running / > 30 days
- 🟡 Yellow = Warning / 7-30 days remaining
- 🔴 Red    = Error / Stopped / < 7 days or expired

### Text Colors
- [cyan]   = Headings and prompts
- [green]  = Success messages
- [yellow] = Warnings
- [red]    = Errors and destructive actions
- [dim]    = Helper text

### Progress Indicators
- ⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏  = Spinner animation
- █ = Filled progress bar
- ░ = Empty progress bar

## Coming Soon Page Preview
```html
Beautiful gradient background (purple to violet)
with animated floating circles

        ┌─────────────────────────────────────┐
        │                                     │
        │         Coming Soon                 │
        │                                     │
        │        example.com                  │
        │                                     │
        │    Something amazing is being       │
        │    built here. Stay tuned for       │
        │    the launch!                      │
        │                                     │
        │             ◯ (spinner)            │
        │                                     │
        └─────────────────────────────────────┘

Features:
✨ Animated gradient background
✨ Floating circles with smooth motion
✨ Fade-in animations
✨ Responsive design
✨ Professional typography
✨ Mobile-friendly
```

## Interactive Features

### Dashboard Updates
- Auto-refreshes every 5 seconds
- Shows real-time changes
- Press Ctrl+C to exit back to menu

### Menu Navigation
- Number keys select options
- 'q' to quit
- Clear visual feedback for all actions

### Confirmation Prompts
- Destructive actions require explicit confirmation
- Can cancel at any time
- Clear indication of what will be affected

### Error Handling
- Clear error messages in red
- Helpful suggestions for fixes
- Never crashes - always recoverable

## Terminal Requirements

Works best with:
- Terminal with 256 color support
- Minimum 80 columns wide
- UTF-8 encoding (for emojis and symbols)

Tested on:
✅ macOS Terminal.app
✅ iTerm2
✅ VS Code integrated terminal

---

**This is what you'll see when you run the script!**
