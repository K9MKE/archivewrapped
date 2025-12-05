# Archive.org Listening History Wrapped - Web App

A beautiful web application that generates Spotify Wrapped-style presentations from your Archive.org listening history!

## 🌟 Features

### Web Interface
- **Drag & Drop Upload** - Simply drag your ZIP file or click to browse
- **Automatic Processing** - Extracts and analyzes your data automatically
- **Beautiful Slide Show** - Spotify-style presentation with smooth transitions
- **Individual Slide Download** - Save any slide to share on social media
- **Modern Glassmorphism UI** - Contemporary design with blur effects
- **Responsive Design** - Works on desktop, tablet, and mobile

### Visual Enhancements
- **Vibrant Gradient Colors** - Pink, purple, yellow, and green accents
- **Show Artwork Integration** - Fetches official artwork from Archive.org
- **Smooth Animations** - Glassmorphism effects and transitions
- **Rank Badges** - #1, #2, #3 rankings on charts
- **Minutes Display** - Shows minutes with hours in parentheses

### Statistics Included
- Total listening time (hours and days)
- Top 10 artists with listening minutes
- Top 5 shows with artwork
- Personalized insights
- Day of week breakdown
- Monthly listening timeline
- Listening streaks and patterns

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Start the Web Server**
```bash
python app.py
```

3. **Open Your Browser**
Navigate to: **http://localhost:5000**

4. **Upload Your Data**
- Go to Archive.org account settings
- Request your listening history export
- Download the ZIP file
- Drag & drop it into the web app!

## ☁️ Deploy to Render (Free)

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Deploy on Render**
- Go to [Render Dashboard](https://dashboard.render.com)
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Render will auto-detect `render.yaml`
- Click "Create Web Service"
- Wait ~5 minutes for deployment

3. **Done!** Your app will be live at `https://your-app-name.onrender.com`

## 📱 How to Use

1. **Upload** - Drag your Archive.org listening history ZIP file to the upload area
2. **Wait** - The app will extract, analyze, and generate your slides (takes ~10-30 seconds)
3. **Enjoy** - Navigate through your personalized Wrapped presentation!
4. **Share** - Download individual slides to share on social media

### Navigation Controls
- **Arrow Buttons** - Click previous/next arrows
- **Keyboard** - Use ← → arrow keys
- **Touch** - Swipe left/right on mobile
- **Dots** - Click any dot to jump to that slide
- **Download** - Save the current slide
- **Restart** - Upload a new file

## 🎨 Slide Sequence

1. **Title** - Welcome to your 2025 Wrapped
2. **Listening Time** - Total hours listened
3. **#1 Artist** - Your most-played artist
4. **Top 10 Artists** - Colorful chart with rankings
5. **Top Show** - Your most-played concert
6. **Day of Week** - When you listen most
7. **Biggest Day** - Your marathon listening day
8. **Stats Summary** - All your numbers
9. **Monthly Timeline** - Your listening journey
10. **Finale** - Celebration and summary

## 🎯 2025 Data Only

The app automatically filters your listening history to show only 2025 data, giving you a true year-in-review experience!

## 🛠 Technical Details

- **Backend**: Flask (Python web framework)
- **Data Analysis**: Pandas
- **Visualization**: Matplotlib, Seaborn
- **Frontend**: HTML5, CSS3, JavaScript
- **File Handling**: Automatic ZIP extraction
- **Design**: Spotify-inspired dark theme with gradients

## 📂 Project Structure

```
archivewrapped/
├── app.py                  # Flask web server
├── analyze.py              # Data analysis engine
├── generate_wrapped.py     # Slide generation
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Web interface
├── static/
│   ├── style.css          # Styling
│   ├── script.js          # Frontend logic
│   └── generated/         # Generated slides
├── uploads/               # Temporary uploads
├── output/                # CLI output folder
└── data/                  # Data files
```

## 🎨 Color Scheme

- **Primary Green**: #1DB954 (Spotify green)
- **Accent Green**: #1ed760
- **Pink**: #ff6b9d
- **Purple**: #c06cf5
- **Yellow**: #ffc864
- **Dark Background**: #0a0a0a with gradients

## 🔧 Troubleshooting

**Upload fails?**
- Make sure you're uploading the ZIP file from Archive.org
- Check that it contains: ListeningHistorySummary.tsv, Favorites.tsv, DetailedListeningHistory.json

**Slides look weird?**
- Make sure you have matplotlib and required fonts installed
- Try refreshing the page

**Port already in use?**
- Change the port in app.py: `app.run(debug=True, port=5001)`

## 📄 License

MIT License - feel free to use and modify!

## 🎉 Enjoy Your Wrapped!

Share your stats on social media and tag @archiveorg to show your support for live music preservation!
