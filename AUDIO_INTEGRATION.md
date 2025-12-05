# Audio Integration Notes

## Archive.org Audio Playback

To add audio snippets from Archive.org recordings:

### Option 1: Direct Archive.org URLs
Archive.org provides audio files in multiple formats. For a recording ID like "ACB2025-09-12":
- MP3: `https://archive.org/download/ACB2025-09-12/`
- Then look for .mp3 files in the item's file list

### Option 2: Embed Archive.org Player
```html
<iframe src="https://archive.org/embed/ACB2025-09-12" 
        width="500" height="30" frameborder="0" webkitallowfullscreen="true" 
        mozallowfullscreen="true" allowfullscreen></iframe>
```

### Implementation Steps:

1. **Fetch recording metadata** from Archive.org API:
   ```
   https://archive.org/metadata/ACB2025-09-12
   ```

2. **Extract audio file URLs** from metadata (look for .mp3 or .flac files)

3. **Add HTML5 audio elements** to each slide:
   ```javascript
   const audio = document.createElement('audio');
   audio.src = audioUrl;
   audio.volume = 0.3;
   audio.loop = false;
   slideDiv.appendChild(audio);
   ```

4. **Control playback** on slide change:
   ```javascript
   function goToSlide(index) {
       // Stop previous slide audio
       const prevAudio = slides[currentSlide].querySelector('audio');
       if (prevAudio) prevAudio.pause();
       
       // Play current slide audio
       const currentAudio = slides[index].querySelector('audio');
       if (currentAudio) currentAudio.play();
   }
   ```

### Challenges:
- Archive.org doesn't have direct "preview snippet" API
- Would need to download full audio files or use their streaming URLs
- Need to handle cases where recordings don't have audio available
- Copyright/licensing considerations for playback

### Alternative:
Use Archive.org's embedded player for each show with custom styling and controls.
