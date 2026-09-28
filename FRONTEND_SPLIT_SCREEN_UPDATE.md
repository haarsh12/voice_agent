# React Frontend Split-Screen Layout Update

## Summary
Updated the React web frontend to display a split-screen layout with voice controls on the left and a real-time auto-scrolling transcript on the right.

## Changes Made

### 1. **VoiceAssistant.tsx** - Split Layout Structure
- Wrapped the voice stage and transcript panel in a new `<div className="split-layout">` container
- This creates a side-by-side layout instead of the previous stacked vertical layout

### 2. **TranscriptPanel.tsx** - Auto-Scroll Functionality
- Added React `useRef` hooks for scroll container and last entry tracking
- Implemented `useEffect` that triggers when new entries are added
- Auto-scrolls to the latest message using `scrollIntoView()` with smooth behavior
- Wrapped transcript content in a scrollable container `<div className="transcript-scroll-container">`

### 3. **App.css** - Split-Screen Styling

#### Main Layout Changes:
```css
/* Full-width app container */
.voice-app { width: 100%; }

/* Split layout: 40% left (voice), 60% right (transcript) */
.split-layout { 
  display: grid; 
  grid-template-columns: 40% 60%; 
  gap: 24px; 
  height: calc(100vh - 140px);
}
```

#### Voice Stage Updates:
- Changed from fixed `max-width: 680px` to `max-width: 100%`
- Removed auto margin for left alignment
- Added `overflow-y: auto` for scrolling when content overflows

#### Transcript Panel Updates:
- Changed to `width: 100%` and `height: 100%` to fill grid cell
- Removed auto margin
- Made it a flex container to enable scrollable content area
- Added `.transcript-scroll-container` with custom scrollbar styling

#### Responsive Design:
- **Tablets (< 1024px)**: Switches to single column layout (stacked)
- **Mobile (< 640px)**: Maintains readability with adjusted heights

## Features Implemented

✅ **Split-screen layout**: Voice controls (left 40%) and transcript (right 60%)  
✅ **Auto-scroll**: New messages automatically scroll into view smoothly  
✅ **Real-time display**: All conversation messages visible as they arrive  
✅ **Custom scrollbar**: Styled scrollbar matching the app theme  
✅ **Responsive**: Adapts to tablet/mobile with stacked layout  
✅ **User/Assistant labels**: Each message clearly labeled (You/Vyamit)  

## How It Works

1. **Layout**: CSS Grid creates two columns (40/60 split)
2. **Auto-scroll**: React `useEffect` watches `entries` array changes
3. **Scroll behavior**: Uses `scrollIntoView({ behavior: 'smooth' })` on last message
4. **Overflow handling**: Transcript container has `overflow-y: auto` for scrolling

## Testing

To see the changes:
```bash
cd frontend
npm run dev
```

Open browser and:
1. Connect to the voice assistant
2. Start speaking - your transcript appears on the right
3. Watch messages auto-scroll as new text arrives
4. All conversation history remains visible with scroll

## Technical Details

- **Framework**: React + TypeScript + Vite
- **UI Library**: LiveKit Components React
- **Styling**: CSS Grid + Flexbox
- **Auto-scroll**: Native `scrollIntoView()` API
- **State Management**: React hooks (useRef, useEffect)
