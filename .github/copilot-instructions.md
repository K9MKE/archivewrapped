<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Archive.org Listening History Wrapped - Web App

An interactive web application that generates Spotify Wrapped-style presentations from Archive.org listening history.

## Project Features

### Web Interface (app.py)
- Drag & drop ZIP file upload
- Automatic extraction and processing
- Real-time slide generation
- Individual slide downloads
- Responsive design with mobile support

### Data Analysis (analyze.py)
- Filters to 2025 data only
- Calculates listening statistics
- Top artists, shows, and days
- Monthly and weekly breakdowns

### Visual Presentation (generate_wrapped.py)
- 10 professionally designed slides
- Vibrant gradient color scheme
- Artist avatars with gradient circles
- Rank badges in circular borders
- Shadow effects and text glow
- No emoji rendering issues (uses Unicode symbols)
- Proper spacing to prevent text overlap

### Technical Stack
- Backend: Flask web framework
- Frontend: HTML5, CSS3, vanilla JavaScript
- Data: Pandas for analysis
- Visuals: Matplotlib, Seaborn, Pillow
- Design: Spotify-inspired dark theme

## Setup Complete ✓
- [x] Web application with drag & drop upload
- [x] Automatic ZIP extraction
- [x] 2025 data filtering
- [x] Visual slide generation with artist imagery
- [x] Fixed layout issues (WRAPPED visibility, chart spacing)
- [x] Interactive slideshow with multiple navigation methods
- [x] Individual slide download capability
- [x] Responsive mobile-friendly design
