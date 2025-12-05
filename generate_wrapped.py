"""
Generate a visual Spotify Wrapped-style presentation
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for web app compatibility
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
import seaborn as sns
from PIL import Image
import os
from analyze import ListeningHistoryAnalyzer
import numpy as np
from matplotlib import patheffects
import gc  # Garbage collection for memory management

# Set style
plt.style.use('dark_background')
sns.set_palette("husl")

# Reduce matplotlib memory usage aggressively
matplotlib.rcParams['figure.max_open_warning'] = 0
matplotlib.rcParams['agg.path.chunksize'] = 10000
matplotlib.rcParams['path.simplify'] = True
matplotlib.rcParams['path.simplify_threshold'] = 1.0

# Reduce font cache size
matplotlib.rcParams['font.size'] = 10

class WrappedPresentation:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.output_dir = 'output'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Color scheme (Vibrant Spotify-ish with gradients)
        self.colors = {
            'primary': '#1DB954',
            'secondary': '#191414',
            'accent': '#1ed760',
            'accent2': '#ff6b9d',
            'accent3': '#c06cf5',
            'accent4': '#ffc864',
            'text': '#FFFFFF',
            'background': '#0a0a0a',
            'gradient1': '#1a1a2e',
            'gradient2': '#16213e'
        }
    
    def _get_artist_image(self, artist_name):
        """Try to get artist image - placeholder for now, can be enhanced with API calls"""
        # For now, create a colorful gradient circle as artist avatar
        # In the future, this could fetch from MusicBrainz, Last.fm, or Archive.org APIs
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a gradient circle with artist initial
            size = 400
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Choose color based on artist name hash
            colors = [
                [(29, 185, 84), (30, 215, 96)],      # Green gradient
                [(255, 107, 157), (192, 108, 245)],  # Pink to purple
                [(192, 108, 245), (255, 200, 100)],  # Purple to yellow
                [(30, 215, 96), (255, 200, 100)]     # Green to yellow
            ]
            color_idx = hash(artist_name) % len(colors)
            gradient_colors = colors[color_idx]
            
            # Draw gradient circle
            for i in range(size):
                ratio = i / size
                r = int(gradient_colors[0][0] + (gradient_colors[1][0] - gradient_colors[0][0]) * ratio)
                g = int(gradient_colors[0][1] + (gradient_colors[1][1] - gradient_colors[0][1]) * ratio)
                b = int(gradient_colors[0][2] + (gradient_colors[1][2] - gradient_colors[0][2]) * ratio)
                draw.ellipse([i//2, i//2, size-i//2, size-i//2], fill=(r, g, b, 255))
            
            # Add artist initial
            try:
                initial = artist_name[0].upper()
                font = ImageFont.truetype("arial.ttf", 200)
            except:
                initial = artist_name[0].upper()
                font = ImageFont.load_default()
            
            # Draw initial in center
            bbox = draw.textbbox((0, 0), initial, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size - text_width) // 2
            y = (size - text_height) // 2 - 20
            
            # Draw text with outline
            outline_width = 8
            for adj_x in range(-outline_width, outline_width+1):
                for adj_y in range(-outline_width, outline_width+1):
                    draw.text((x+adj_x, y+adj_y), initial, font=font, fill=(0, 0, 0, 200))
            draw.text((x, y), initial, font=font, fill=(255, 255, 255, 255))
            
            return np.array(img)
        except Exception as e:
            print(f"Could not create artist image: {e}")
            return None
    
    def _create_blurred_background(self, ax, recording_id=None, opacity=0.15):
        """Add a beautiful blurred show artwork as background
        
        DISABLED on production to save processing time and memory.
        """
        # Skip on production
        if not os.environ.get('ENABLE_ARTWORK'):
            return False
            
        if recording_id:
            artwork = self._get_show_artwork(recording_id)
            if artwork is not None:
                from PIL import ImageFilter
                # Convert to PIL, blur, convert back
                pil_img = Image.fromarray(artwork)
                blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=25))
                blurred_array = np.array(blurred)
                # Show as background with low opacity
                ax.imshow(blurred_array, extent=[0, 10, 0, 10], aspect='auto', alpha=opacity, zorder=0)
                return True
        return False
    
    def _get_show_artwork(self, recording_id):
        """Fetch show artwork from Archive.org using official APIs
        
        DISABLED on production to reduce memory and processing time.
        Enable locally by setting ENABLE_ARTWORK environment variable.
        """
        # Skip artwork fetching on production servers to save memory and time
        if not os.environ.get('ENABLE_ARTWORK'):
            return None
            
        try:
            import urllib.request
            import json
            from PIL import Image
            import io
            
            # Method 1: Try using official Metadata API to find image files
            # API endpoint: https://archive.org/metadata/{identifier}
            try:
                metadata_url = f"https://archive.org/metadata/{recording_id}"
                with urllib.request.urlopen(metadata_url, timeout=5) as response:
                    metadata = json.loads(response.read())
                    
                    # Look through files for image files
                    # Prefer: itemimage.jpg, {identifier}.jpg, __ia_thumb.jpg, or any .jpg/.png
                    if 'files' in metadata:
                        image_files = []
                        for file in metadata['files']:
                            filename = file.get('name', '').lower()
                            file_format = file.get('format', '').lower()
                            
                            # Prioritize cover images
                            if 'itemimage' in filename or filename == f"{recording_id.lower()}.jpg":
                                image_files.insert(0, file['name'])  # Highest priority
                            elif 'jpg' in filename or 'jpeg' in filename or 'png' in filename:
                                image_files.append(file['name'])
                            elif 'jpeg' in file_format or 'png' in file_format:
                                image_files.append(file['name'])
                        
                        # Try to download the best image file
                        for image_file in image_files:
                            try:
                                # Official archival URL pattern
                                image_url = f"https://archive.org/download/{recording_id}/{image_file}"
                                with urllib.request.urlopen(image_url, timeout=5) as img_response:
                                    image_data = img_response.read()
                                    img = Image.open(io.BytesIO(image_data))
                                    img = img.convert('RGBA')
                                    img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                                    return np.array(img)
                            except:
                                continue  # Try next image file
            except:
                pass  # Fall through to Method 2
            
            # Method 2: Fallback - try common image filenames using archival URLs
            common_names = [
                f"{recording_id}.jpg",
                f"{recording_id.lower()}.jpg",
                "itemimage.jpg",
                "__ia_thumb.jpg"
            ]
            
            for filename in common_names:
                try:
                    # Official archival URL: https://archive.org/download/{identifier}/{filename}
                    url = f"https://archive.org/download/{recording_id}/{filename}"
                    with urllib.request.urlopen(url, timeout=5) as response:
                        image_data = response.read()
                        img = Image.open(io.BytesIO(image_data))
                        img = img.convert('RGBA')
                        img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                        return np.array(img)
                except:
                    continue
            
            return None  # No artwork found
                
        except Exception as e:
            print(f"Could not fetch show artwork for {recording_id}: {e}")
            return None
    
    def _add_90s_background(self, ax):
        """Add 90s-style geometric background pattern"""
        from matplotlib.patches import Rectangle, Polygon, Circle
        import random
        
        # Colorful grid squares
        pattern_colors = [self.colors['primary'], self.colors['accent2'], 
                         self.colors['accent3'], self.colors['accent4']]
        for i in range(0, 11, 1):
            for j in range(0, 11, 1):
                if (i + j) % 3 == 0:
                    color = pattern_colors[(i * j) % len(pattern_colors)]
                    rect = Rectangle((i, j), 0.8, 0.8, 
                                    facecolor=color, 
                                    alpha=0.12, zorder=0,
                                    edgecolor=color, linewidth=0.5)
                    ax.add_patch(rect)
        
        # Diagonal striped lines (Memphis style)
        for i in range(-10, 20, 2):
            line_x = [i, i+1.5]
            line_y = [0, 10]
            ax.plot(line_x, line_y, color=self.colors['primary'], 
                   alpha=0.15, linewidth=3, zorder=0, linestyle='-')
            # Add complementary diagonal
            ax.plot([i+0.5, i+2], line_y, color=self.colors['accent2'], 
                   alpha=0.1, linewidth=2, zorder=0, linestyle='-')
        
        # Random geometric shapes for texture
        random.seed(42)  # Consistent pattern
        for _ in range(15):
            x, y = random.uniform(0, 10), random.uniform(0, 10)
            size = random.uniform(0.4, 0.9)
            shape_type = random.choice(['triangle', 'circle', 'square'])
            color = random.choice(pattern_colors)
            
            if shape_type == 'triangle':
                triangle = Polygon([[x, y], [x+size, y], [x+size/2, y+size]], 
                                 facecolor=color, alpha=0.1, zorder=0,
                                 edgecolor=color, linewidth=1.5)
                ax.add_patch(triangle)
            elif shape_type == 'circle':
                circle = Circle((x, y), size/2, facecolor=color, 
                              alpha=0.08, zorder=0, edgecolor=color, linewidth=1)
                ax.add_patch(circle)
            else:
                square = Rectangle((x, y), size, size, facecolor=color, 
                                 alpha=0.09, zorder=0, edgecolor=color, linewidth=1)
                ax.add_patch(square)
    
    def create_title_slide(self):
        """Create title/intro slide"""
        fig, ax = plt.subplots(figsize=(12, 8), facecolor=self.colors['background'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Add show artwork background
        top_shows = self.analyzer.get_top_shows(1)
        if len(top_shows) > 0 and 'recording_id' in top_shows.columns:
            self._create_blurred_background(ax, top_shows.iloc[0]['recording_id'], opacity=0.2)
        
        # Add 90s background
        self._add_90s_background(ax)
        
        # Add decorative circles
        circle1 = Circle((2, 8), 0.8, color=self.colors['accent2'], alpha=0.3)
        circle2 = Circle((8, 2), 1.2, color=self.colors['accent3'], alpha=0.2)
        circle3 = Circle((1.5, 2.5), 0.6, color=self.colors['accent4'], alpha=0.25)
        ax.add_patch(circle1)
        ax.add_patch(circle2)
        ax.add_patch(circle3)
        
        # Title with glow effect
        title1 = ax.text(5, 6.5, 'Archive.org', 
                ha='center', va='center', 
                fontsize=60, fontweight='bold',
                color=self.colors['primary'])
        title1.set_path_effects([patheffects.withStroke(linewidth=3, foreground=self.colors['accent'], alpha=0.5)])
        
        title2 = ax.text(5, 5.5, 'WRAPPED', 
                ha='center', va='center', 
                fontsize=90, fontweight='bold',
                color=self.colors['text'])
        title2.set_path_effects([patheffects.withStroke(linewidth=4, foreground=self.colors['primary'], alpha=0.6)])
        
        year_text = ax.text(5, 4, '2025', 
                ha='center', va='center', 
                fontsize=50, fontweight='bold',
                color=self.colors['accent'])
        year_text.set_path_effects([patheffects.withStroke(linewidth=2, foreground=self.colors['accent2'], alpha=0.4)])
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '01_title.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created title slide")
    
    def create_listening_time_slide(self):
        """Create slide showing total listening time"""
        total_time = self.analyzer.get_total_listening_time()
        
        fig, ax = plt.subplots(figsize=(12, 8), facecolor=self.colors['background'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Add show artwork background from top 2 shows
        top_shows = self.analyzer.get_top_shows(2)
        if len(top_shows) > 1 and 'recording_id' in top_shows.columns:
            self._create_blurred_background(ax, top_shows.iloc[1]['recording_id'], opacity=0.18)
        
        # Add 90s background
        self._add_90s_background(ax)
        
        # Add decorative elements
        circle1 = Circle((8.5, 7.5), 0.5, color=self.colors['accent3'], alpha=0.25)
        circle2 = Circle((1.5, 3), 0.7, color=self.colors['accent2'], alpha=0.2)
        ax.add_patch(circle1)
        ax.add_patch(circle2)
        
        text1 = ax.text(5, 7.5, 'In 2025, you listened to', 
                ha='center', va='center', 
                fontsize=38,
                color=self.colors['text'], alpha=0.9)
        
        hours_text = ax.text(5, 5, f"{total_time['total_hours']:,.0f}", 
                ha='center', va='center', 
                fontsize=140, fontweight='bold',
                color=self.colors['primary'])
        hours_text.set_path_effects([patheffects.withStroke(linewidth=5, foreground=self.colors['accent'], alpha=0.4)])
        
        ax.text(5, 3.5, 'hours of live music', 
                ha='center', va='center', 
                fontsize=42,
                color=self.colors['text'])
        
        days_text = ax.text(5, 2.3, f"That's {total_time['total_days']:.1f} full days!", 
                ha='center', va='center', 
                fontsize=34, fontweight='bold',
                color=self.colors['accent2'])
        days_text.set_path_effects([patheffects.withStroke(linewidth=2, foreground=self.colors['accent4'], alpha=0.3)])
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '02_listening_time.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created listening time slide")
    
    def create_top_artist_slide(self):
        """Create slide for #1 artist"""
        top_artists = self.analyzer.get_top_artists(1)
        artist = top_artists.iloc[0]
        
        fig, ax = plt.subplots(figsize=(12, 8), facecolor=self.colors['background'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Add 90s background
        self._add_90s_background(ax)
        
        # Decorative elements - use diverse shapes instead of just circles
        from matplotlib.patches import Polygon, FancyBboxPatch, Wedge
        
        # Hexagons
        hex_points = [[1.2, 7.2], [1.5, 7.5], [1.8, 7.2], [1.8, 6.8], [1.5, 6.5], [1.2, 6.8]]
        hex1 = Polygon(hex_points, facecolor=self.colors['accent2'], alpha=0.3, zorder=1)
        ax.add_patch(hex1)
        
        # Rounded rectangles
        fancy_box = FancyBboxPatch((8, 5.5), 1.2, 0.8, boxstyle="round,pad=0.1",
                                  facecolor=self.colors['accent3'], alpha=0.25, zorder=1)
        ax.add_patch(fancy_box)
        
        # Pie wedges
        wedge1 = Wedge((2.5, 2.8), 0.6, 45, 180, facecolor=self.colors['accent4'], alpha=0.3, zorder=1)
        wedge2 = Wedge((8.2, 2.2), 0.5, 0, 135, facecolor=self.colors['accent'], alpha=0.25, zorder=1)
        ax.add_patch(wedge1)
        ax.add_patch(wedge2)
        
        # Add artist image circle if available
        artist_image = self._get_artist_image(artist['artistName'])
        if artist_image is not None:
            try:
                from matplotlib.offsetbox import OffsetImage, AnnotationBbox
                # Create circular image
                imagebox = OffsetImage(artist_image, zoom=0.25)
                imagebox.image.axes = ax
                ab = AnnotationBbox(imagebox, (5, 8.5), frameon=False)
                ax.add_artist(ab)
                header_y = 7.0
            except Exception as e:
                # Star effect with #1
                star = ax.text(5, 8.2, '★', ha='center', va='center', fontsize=80, 
                              color=self.colors['accent4'], fontweight='bold')
                star.set_path_effects([patheffects.withStroke(linewidth=3, foreground=self.colors['accent2'], alpha=0.5)])
                header_y = 7.2
        else:
            # Star effect with #1
            star = ax.text(5, 8.2, '★', ha='center', va='center', fontsize=80, 
                          color=self.colors['accent4'], fontweight='bold')
            star.set_path_effects([patheffects.withStroke(linewidth=3, foreground=self.colors['accent2'], alpha=0.5)])
            header_y = 7.2
        
        header = ax.text(5, header_y, 'Your #1 Artist', 
                ha='center', va='center', 
                fontsize=42, fontweight='bold',
                color=self.colors['accent4'])
        header.set_path_effects([patheffects.withStroke(linewidth=2, foreground=self.colors['accent2'], alpha=0.3)])
        
        artist_text = ax.text(5, 5, artist['artistName'], 
                ha='center', va='center', 
                fontsize=70, fontweight='bold',
                color=self.colors['primary'])
        artist_text.set_path_effects([patheffects.withStroke(linewidth=6, foreground=self.colors['accent'], alpha=0.5)])
        
        # Format time as minutes with hours in parenthesis if over 1 hour
        total_minutes = int(artist['total_hours'] * 60)
        if artist['total_hours'] >= 1:
            time_label = f"{total_minutes} minutes ({artist['total_hours']:.1f} hours)"
        else:
            time_label = f"{total_minutes} minutes"
        
        hours = ax.text(5, 3.3, time_label, 
                ha='center', va='center', 
                fontsize=56, fontweight='bold',
                color=self.colors['accent2'])
        hours.set_path_effects([patheffects.withStroke(linewidth=3, foreground=self.colors['accent3'], alpha=0.4)])
        
        ax.text(5, 2.3, f"{artist['session_count']} listening sessions", 
                ha='center', va='center', 
                fontsize=32,
                color=self.colors['text'], alpha=0.9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '03_top_artist.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created top artist slide")
    
    def create_top_artists_chart(self):
        """Create chart of top 10 artists with artwork backgrounds"""
        top_artists = self.analyzer.get_top_artists(10)
        
        # Convert hours to minutes for display
        top_artists['total_minutes'] = top_artists['total_hours'] * 60
        
        fig, ax = plt.subplots(figsize=(12, 8), facecolor=self.colors['background'])
        
        # Add subtle background pattern
        from matplotlib.patches import Rectangle
        for i in range(0, 20, 2):
            rect = Rectangle((0, i/2), 100, 0.5, facecolor=self.colors['gradient1'], alpha=0.15, zorder=0)
            ax.add_patch(rect)
        
        # Horizontal bar chart with gradient colors
        y_pos = np.arange(len(top_artists))
        colors_gradient = [self.colors['primary'], self.colors['accent'], self.colors['accent2'], 
                          self.colors['accent3'], self.colors['accent4']]
        bar_colors = [colors_gradient[i % len(colors_gradient)] for i in range(len(top_artists))]
        
        bars = ax.barh(y_pos, top_artists['total_minutes'], 
                       color=bar_colors, alpha=0.9, edgecolor='white', linewidth=1.5, zorder=3)
        
        # Shadow effect on bars
        for i, bar in enumerate(bars):
            bar.set_path_effects([patheffects.withSimplePatchShadow(offset=(3, -3), shadow_rgbFace='black', alpha=0.4)])
        
        # Configure clean y-axis with artist names
        ax.set_yticks(y_pos)
        ax.set_yticklabels(top_artists['artistName'], fontsize=14, fontweight='bold', color=self.colors['text'])
        ax.invert_yaxis()
        ax.set_xlabel('Minutes Listened', fontsize=20, color=self.colors['accent4'], fontweight='bold')
        title = ax.set_title('Your Top 10 Artists of 2025', fontsize=38, fontweight='bold', 
                     color=self.colors['primary'], pad=30)
        title.set_path_effects([patheffects.withStroke(linewidth=4, foreground=self.colors['accent2'], alpha=0.5)])
        
        # Clean modern styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.colors['text'])
        ax.spines['bottom'].set_color(self.colors['text'])
        ax.tick_params(colors=self.colors['text'], labelsize=14, length=0, pad=10)
        ax.set_facecolor(self.colors['background'])
        ax.grid(axis='x', alpha=0.15, color=self.colors['text'], linestyle='--', zorder=1)
        
        # Add rank badges and time labels (minutes with hours in parenthesis if over 1 hour)
        max_minutes = top_artists['total_minutes'].max()
        
        for i, (idx, row) in enumerate(top_artists.iterrows()):
            # Rank badge to the left of y-axis
            rank_color = self.colors['accent4'] if i == 0 else self.colors['primary']
            ax.text(-max_minutes * 0.12, i, f"#{i+1}", va='center', ha='center', fontsize=18, 
                   color='white', fontweight='bold', zorder=5,
                   bbox=dict(boxstyle='circle,pad=0.5', facecolor=rank_color, 
                            edgecolor='white', linewidth=2.5, alpha=0.95))
            
            # Time label at end of bar - minutes with hours in parenthesis if over 1 hour
            minutes = int(row['total_minutes'])
            hours = row['total_hours']
            if hours >= 1:
                time_label = f"{minutes} min ({hours:.1f}h)"
            else:
                time_label = f"{minutes} min"
            
            ax.text(row['total_minutes'] + (max_minutes * 0.015), i, time_label, 
                   va='center', ha='left', fontsize=15, color=self.colors['accent4'], 
                   fontweight='bold', zorder=5,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=self.colors['background'], 
                            edgecolor=self.colors['accent4'], linewidth=1.5, alpha=0.8))
        
        # Set limits with proper margins
        ax.set_xlim(-max_minutes * 0.15, max_minutes * 1.15)
        plt.tight_layout(pad=2)
        plt.subplots_adjust(left=0.25)
        plt.savefig(os.path.join(self.output_dir, '04_top_artists_chart.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created top artists chart")
    
    def create_top_show_slide(self):
        """Create slide for top show"""
        top_shows = self.analyzer.get_top_shows(1)
        show = top_shows.iloc[0]
        
        fig, ax = plt.subplots(figsize=(12, 8), facecolor=self.colors['background'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Try to get show artwork from Archive.org
        # Try to get show artwork from Archive.org
        try:
            recording_id = show.get('recording_id', None)
            if recording_id:
                show_artwork = self._get_show_artwork(recording_id)
                if show_artwork is not None:
                    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
                    # Display artwork at top
                    imagebox = OffsetImage(show_artwork, zoom=0.35)
                    imagebox.image.axes = ax
                    ab = AnnotationBbox(imagebox, (5, 8.2), frameon=False,
                                       box_alignment=(0.5, 0.5))
                    ax.add_artist(ab)
                    title_y = 6.3
                else:
                    title_y = 8
            else:
                title_y = 8
        except Exception as e:
            print(f"Could not load show artwork: {e}")
            title_y = 8
        
        ax.text(5, title_y, 'Your Most-Played Show', 
                ha='center', va='center', 
                fontsize=40,
                color=self.colors['text'])
        
        # Adjust all text positions relative to title
        artist_y = title_y - 1.8
        date_y = title_y - 2.8
        venue_y = title_y - 3.8
        location_y = title_y - 4.5
        hours_y = title_y - 5.5
        count_y = title_y - 6.3
        
        ax.text(5, artist_y, show['artist'], 
                ha='center', va='center', 
                fontsize=50, fontweight='bold',
                color=self.colors['primary'])
        
        ax.text(5, date_y, show['date'], 
                ha='center', va='center', 
                fontsize=35,
                color=self.colors['accent'])
        
        ax.text(5, venue_y, show['venue'], 
                ha='center', va='center', 
                fontsize=28,
                color=self.colors['text'])
        
        if show['location'] and show['location'] != 'Unknown':
            ax.text(5, location_y, show['location'], 
                    ha='center', va='center', 
                    fontsize=24,
                    color=self.colors['text'], alpha=0.8)
        
        # Format time as minutes with hours in parenthesis if over 1 hour
        total_minutes = int(show['total_hours'] * 60)
        if show['total_hours'] >= 1:
            time_label = f"{total_minutes} minutes ({show['total_hours']:.1f} hours)"
        else:
            time_label = f"{total_minutes} minutes"
        
        ax.text(5, hours_y, time_label, 
                ha='center', va='center', 
                fontsize=40,
                color=self.colors['accent'])
        
        ax.text(5, count_y, f"Listened {show['listen_count']} times", 
                ha='center', va='center', 
                fontsize=25,
                color=self.colors['text'])
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '05_top_show.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created insights slide")
    
    def create_show_gallery_slides(self):
        """Create single slide showing top 5 shows with artwork"""
        # Get top 5 shows only
        top_shows = self.analyzer.get_top_shows(5)
        
        fig = plt.figure(figsize=(12, 8), facecolor=self.colors['background'])
        
        # Title
        title_ax = fig.add_axes([0.05, 0.92, 0.9, 0.06])
        title_ax.set_xlim(0, 10)
        title_ax.set_ylim(0, 1)
        title_ax.axis('off')
        title = title_ax.text(5, 0.5, 'Your Top 5 Shows of 2025', ha='center', va='center',
                            fontsize=44, fontweight='bold', color=self.colors['primary'])
        title.set_path_effects([patheffects.withStroke(linewidth=4, foreground=self.colors['accent2'], alpha=0.5)])
        
        # Create 5 horizontal panels
        panel_height = 0.16
        panel_spacing = 0.01
        start_y = 0.72
        
        from matplotlib.patches import Rectangle
        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
        
        accent_colors = [self.colors['accent4'], self.colors['accent2'], self.colors['accent3'], 
                        self.colors['primary'], self.colors['accent']]
        
        for i, (_, show) in enumerate(top_shows.iterrows()):
            panel_y = start_y - (i * (panel_height + panel_spacing))
            ax = fig.add_axes([0.05, panel_y, 0.9, panel_height])
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 10)
            ax.axis('off')
            
            # Gradient background
            for x in range(0, 100, 4):
                alpha = 0.15 - (x / 1000)
                rect = Rectangle((x, 0), 4, 10, facecolor=accent_colors[i], alpha=alpha, zorder=1)
                ax.add_patch(rect)
            
            # Rank badge
            rank_circle = Circle((8, 5), 3, facecolor=accent_colors[i], 
                               edgecolor='white', linewidth=3, alpha=0.95, zorder=3)
            ax.add_patch(rank_circle)
            ax.text(8, 5, f"#{i+1}", ha='center', va='center', fontsize=28, 
                   color='white', fontweight='bold', zorder=4)
            
            # Try to get show artwork
            recording_id = show.get('recording_id', None)
            artwork_x = 20
            if recording_id:
                show_artwork = self._get_show_artwork(recording_id)
                if show_artwork is not None:
                    # Calculate zoom to ensure consistent display size regardless of image dimensions
                    # Target display size: ~175 pixels (500 * 0.35)
                    target_size = 175
                    img_height, img_width = show_artwork.shape[:2]
                    max_dimension = max(img_height, img_width)
                    zoom_factor = target_size / max_dimension
                    
                    imagebox = OffsetImage(show_artwork, zoom=zoom_factor)
                    imagebox.image.axes = ax
                    ab = AnnotationBbox(imagebox, (artwork_x, 5), frameon=True, 
                                      box_alignment=(0.5, 0.5),
                                      bboxprops=dict(edgecolor='white', linewidth=2.5, facecolor='none'))
                    ax.add_artist(ab)
                    artwork_x = 32
            
            # Show info
            ax.text(artwork_x, 7, show['artist'], ha='left', va='center',
                   fontsize=18, fontweight='bold', color='white', zorder=4,
                   path_effects=[patheffects.withStroke(linewidth=2, foreground='black')])
            
            ax.text(artwork_x, 4.5, show['date'], ha='left', va='center',
                   fontsize=14, color=self.colors['accent2'], zorder=4,
                   path_effects=[patheffects.withStroke(linewidth=1.5, foreground='black')])
            
            ax.text(artwork_x, 2, f"{show['venue']}", ha='left', va='center',
                   fontsize=11, color=self.colors['text'], alpha=0.9, zorder=4)
            
            # Stats on right - minutes with hours in parenthesis if over 1 hour
            stats_x = 78
            total_minutes = int(show['total_hours'] * 60)
            if show['total_hours'] >= 1:
                time_label = f"{total_minutes} min ({show['total_hours']:.1f}h)"
            else:
                time_label = f"{total_minutes} min"
            
            ax.text(stats_x, 6.5, time_label, ha='center', va='center',
                   fontsize=24, fontweight='bold', color=accent_colors[i], zorder=4,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor=self.colors['gradient2'],
                            edgecolor=accent_colors[i], linewidth=2.5, alpha=0.9))
            
            ax.text(stats_x, 3, f"{show['listen_count']} plays", ha='center', va='center',
                   fontsize=12, color=self.colors['text'], alpha=0.85, zorder=4)
        
        plt.savefig(os.path.join(self.output_dir, '05_top_shows.png'),
                   dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created top 5 shows slide")
        
        return 1
    
    def create_day_of_week_chart(self):
        """Create chart showing listening by day of week"""
        day_stats = self.analyzer.get_listening_by_day()
        
        fig, ax = plt.subplots(figsize=(12, 8), facecolor=self.colors['background'])
        
        # Add show artwork background
        top_shows = self.analyzer.get_top_shows(3)
        if len(top_shows) > 2 and 'recording_id' in top_shows.columns:
            self._create_blurred_background(ax, top_shows.iloc[2]['recording_id'], opacity=0.12)
        
        # Create modern gradient bars
        colors_list = [self.colors['accent2'], self.colors['accent3'], self.colors['accent4'],
                      self.colors['primary'], self.colors['accent'], self.colors['accent2'], self.colors['accent3']]
        
        bars = ax.bar(range(len(day_stats)), day_stats['total_minutes'], 
                      color=colors_list[:len(day_stats)], alpha=0.9, edgecolor='white', linewidth=2)
        
        # Add glow effect to bars
        for bar in bars:
            bar.set_path_effects([patheffects.withSimplePatchShadow(offset=(0, -3), shadow_rgbFace='white', alpha=0.3)])
        
        # Highlight the top day with extra glow
        max_idx = day_stats['total_minutes'].idxmax()
        bars[max_idx].set_alpha(1.0)
        bars[max_idx].set_linewidth(4)
        
        ax.set_xticks(range(len(day_stats)))
        ax.set_xticklabels(day_stats['day'], fontsize=16, fontweight='bold')
        ax.set_ylabel('Minutes Listened', fontsize=18, color=self.colors['text'], fontweight='bold')
        title = ax.set_title('Your Weekly Rhythm', fontsize=36, fontweight='bold', 
                     color=self.colors['primary'], pad=25)
        title.set_path_effects([patheffects.withStroke(linewidth=4, foreground=self.colors['accent2'], alpha=0.5)])
        
        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.colors['text'])
        ax.spines['bottom'].set_color(self.colors['text'])
        ax.tick_params(colors=self.colors['text'], labelsize=12)
        ax.set_facecolor(self.colors['background'])
        ax.grid(axis='y', alpha=0.2, color=self.colors['text'], linestyle='--', zorder=0)
        
        # Add values on bars with modern styling
        for i, (idx, row) in enumerate(day_stats.iterrows()):
            text = ax.text(i, row['total_minutes'] + (day_stats['total_minutes'].max() * 0.03), 
                          f"{row['total_minutes']:.0f}", 
                          ha='center', fontsize=13, fontweight='bold', color=self.colors['accent4'])
            text.set_path_effects([patheffects.withStroke(linewidth=2, foreground='black', alpha=0.5)])
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '07_day_of_week.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created day of week chart")
    
    def create_top_day_slide(self):
        """Create slide for biggest listening day"""
        top_days = self.analyzer.get_top_listening_days(1)
        day = top_days.iloc[0]
        
        fig, ax = plt.subplots(figsize=(14, 10), facecolor=self.colors['background'])
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis('off')
        
        # Add show artwork background from top show
        top_shows = self.analyzer.get_top_shows(4)
        if len(top_shows) > 3 and 'recording_id' in top_shows.columns:
            self._create_blurred_background(ax, top_shows.iloc[3]['recording_id'], opacity=0.18)
        
        # Modern gradient overlay
        from matplotlib.patches import Rectangle
        for i in range(25):
            alpha = 0.015 - (i * 0.0005)
            rect = Rectangle((0, i*4), 100, 4, facecolor=self.colors['accent3'], alpha=alpha, zorder=1)
            ax.add_patch(rect)
        
        title = ax.text(50, 85, 'Your Biggest Listening Day', 
                ha='center', va='center', 
                fontsize=44, fontweight='bold',
                color=self.colors['primary'])
        title.set_path_effects([patheffects.withStroke(linewidth=5, foreground=self.colors['accent2'], alpha=0.6)])
        
        # Date with glow
        date_text = ax.text(50, 60, str(day['date']), 
                ha='center', va='center', 
                fontsize=62, fontweight='bold',
                color='white')
        date_text.set_path_effects([patheffects.withStroke(linewidth=6, foreground=self.colors['accent4'], alpha=0.8)])
        
        # Hours with modern box
        from matplotlib.patches import FancyBboxPatch
        hours_box = FancyBboxPatch((30, 32), 40, 18,
                                  boxstyle="round,pad=1",
                                  facecolor=self.colors['gradient2'],
                                  edgecolor=self.colors['accent'], 
                                  linewidth=4, alpha=0.9, zorder=2)
        ax.add_patch(hours_box)
        
        ax.text(50, 41, f"{day['total_hours']:.1f} hours", 
                ha='center', va='center', 
                fontsize=48, fontweight='bold',
                color=self.colors['accent'], zorder=3)
        
        ax.text(50, 20, f"{day['session_count']} listening sessions", 
                ha='center', va='center', 
                fontsize=26,
                color=self.colors['text'], alpha=0.9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '08_top_day.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created top day slide")
    
    def create_stats_summary_slide(self):
        """Create summary statistics slide"""
        stats = self.analyzer.get_stats_summary()
        
        fig, ax = plt.subplots(figsize=(14, 10), facecolor=self.colors['background'])
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis('off')
        
        # Add show artwork background
        top_shows = self.analyzer.get_top_shows(5)
        if len(top_shows) > 4 and 'recording_id' in top_shows.columns:
            self._create_blurred_background(ax, top_shows.iloc[4]['recording_id'], opacity=0.15)
        
        title = ax.text(50, 90, 'Your 2025 By The Numbers', 
                ha='center', va='center', 
                fontsize=50, fontweight='bold',
                color=self.colors['primary'])
        title.set_path_effects([patheffects.withStroke(linewidth=5, foreground=self.colors['accent2'], alpha=0.5)])
        
        # Create modern stat cards
        from matplotlib.patches import FancyBboxPatch
        
        stats_data = [
            (f"{stats['unique_artists']}", "Unique Artists", self.colors['accent2']),
            (f"{stats['unique_shows']}", "Unique Shows", self.colors['accent3']),
            (f"{stats['total_sessions']}", "Sessions", self.colors['accent4']),
            (f"{stats['favorite_artists_count']}", "Favorites", self.colors['primary']),
            (f"{stats['favorite_recordings_count']}", "Top Recordings", self.colors['accent'])
        ]
        
        y_start = 70
        card_height = 11
        gap = 2
        
        for i, (number, label, color) in enumerate(stats_data):
            y = y_start - (i * (card_height + gap))
            
            # Modern card with glow
            for offset in range(2, 0, -1):
                glow = FancyBboxPatch((12 - offset*0.4, y - card_height - offset*0.4), 
                                     76 + offset*0.8, card_height + offset*0.8,
                                     boxstyle="round,pad=0.5",
                                     facecolor=color, alpha=0.08, zorder=1)
                ax.add_patch(glow)
            
            card = FancyBboxPatch((12, y - card_height), 76, card_height,
                                 boxstyle="round,pad=0.5",
                                 facecolor=self.colors['gradient2'],
                                 edgecolor=color, linewidth=3.5, alpha=0.95, zorder=2)
            ax.add_patch(card)
            
            # Number - left side
            ax.text(22, y - card_height/2, number, 
                   ha='center', va='center', 
                   fontsize=40, fontweight='bold',
                   color=color, zorder=3)
            
            # Label - right side
            ax.text(55, y - card_height/2, label, 
                   ha='left', va='center', 
                   fontsize=26, fontweight='600',
                   color=self.colors['text'], zorder=3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '09_summary_stats.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created summary stats slide")
    
    def create_monthly_timeline(self):
        """Create timeline of listening by month"""
        monthly_stats = self.analyzer.get_listening_by_month()
        
        fig, ax = plt.subplots(figsize=(14, 8), facecolor=self.colors['background'])
        
        # Line chart with area fill
        x = range(len(monthly_stats))
        ax.plot(x, monthly_stats['total_hours'], 
                color=self.colors['primary'], linewidth=3, marker='o', markersize=6)
        ax.fill_between(x, monthly_stats['total_hours'], alpha=0.3, 
                        color=self.colors['primary'])
        
        # Set labels
        ax.set_xticks(x[::max(1, len(x)//12)])  # Show every Nth month to avoid crowding
        ax.set_xticklabels(monthly_stats['month'].iloc[::max(1, len(monthly_stats)//12)], 
                          rotation=45, ha='right', fontsize=11)
        ax.set_ylabel('Hours Listened', fontsize=16, color=self.colors['text'])
        ax.set_title('Your Listening Journey', fontsize=30, fontweight='bold', 
                     color=self.colors['text'], pad=20)
        
        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.colors['text'])
        ax.spines['bottom'].set_color(self.colors['text'])
        ax.tick_params(colors=self.colors['text'])
        ax.set_facecolor(self.colors['background'])
        ax.grid(True, alpha=0.2, color=self.colors['text'])
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '10_monthly_timeline.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created monthly timeline")
    
    def create_finale_slide(self):
        """Create closing slide"""
        stats = self.analyzer.get_stats_summary()
        
        fig, ax = plt.subplots(figsize=(12, 8), facecolor=self.colors['background'])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Decorative celebration circles
        for x, y, size, color in [
            (2, 7.5, 0.6, self.colors['accent2']),
            (8, 7, 0.5, self.colors['accent3']),
            (1.5, 3.5, 0.7, self.colors['accent4']),
            (8.5, 3, 0.55, self.colors['accent']),
            (3, 2, 0.4, self.colors['primary'])
        ]:
            circle = Circle((x, y), size, color=color, alpha=0.3)
            ax.add_patch(circle)
        
        thanks = ax.text(5, 7.5, 'Your 2025 Wrapped!', 
                ha='center', va='center', 
                fontsize=56, fontweight='bold',
                color=self.colors['primary'])
        thanks.set_path_effects([patheffects.withStroke(linewidth=4, foreground=self.colors['accent'], alpha=0.5)])
        
        ax.text(5, 6.3, '★ You listened to ★', 
                ha='center', va='center', 
                fontsize=32,
                color=self.colors['accent4'], alpha=0.9)
        
        hours = ax.text(5, 5.2, f"{stats['total_hours']:,.0f} hours", 
                ha='center', va='center', 
                fontsize=52, fontweight='bold',
                color=self.colors['accent2'])
        hours.set_path_effects([patheffects.withStroke(linewidth=3, foreground=self.colors['accent3'], alpha=0.4)])
        
        ax.text(5, 4.2, f"{stats['unique_artists']} artists · {stats['unique_shows']} shows", 
                ha='center', va='center', 
                fontsize=38,
                color=self.colors['text'])
        
        closing = ax.text(5, 2.5, '♪ Keep the music playing! ♪', 
                ha='center', va='center', 
                fontsize=36, fontweight='bold',
                color=self.colors['accent'])
        closing.set_path_effects([patheffects.withStroke(linewidth=2, foreground=self.colors['accent4'], alpha=0.3)])
        
        ax.text(5, 1.5, 'See you in 2026!', 
                ha='center', va='center', 
                fontsize=28,
                color=self.colors['text'], alpha=0.8)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '11_finale.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created finale slide")
    
    def create_insights_slide(self):
        """Create personalized insights slide with modern design"""
        insights = self.analyzer.get_personalized_insights()
        
        fig, ax = plt.subplots(figsize=(14, 12), facecolor=self.colors['background'])
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis('off')
        
        # Try to add a show artwork background
        top_shows = self.analyzer.get_top_shows(1)
        if len(top_shows) > 0 and 'recording_id' in top_shows.columns:
            self._create_blurred_background(ax, top_shows.iloc[0]['recording_id'], opacity=0.12)
        
        # Modern gradient overlay
        from matplotlib.patches import Rectangle
        for i in range(20):
            alpha = 0.02 - (i * 0.001)
            rect = Rectangle((0, i*5), 100, 5, facecolor=self.colors['primary'], alpha=alpha, zorder=1)
            ax.add_patch(rect)
        
        # Title with modern styling
        title = ax.text(50, 92, 'Your Listening DNA', 
                ha='center', va='center', 
                fontsize=52, fontweight='bold',
                color=self.colors['primary'])
        title.set_path_effects([patheffects.withStroke(linewidth=5, foreground=self.colors['accent2'], alpha=0.6)])
        
        ax.text(50, 86, 'What makes your year unique', 
                ha='center', va='center', 
                fontsize=22, style='italic',
                color=self.colors['text'], alpha=0.7)
        
        # Display insights in modern card grid
        from matplotlib.patches import FancyBboxPatch
        
        # Determine layout based on insight count
        num_insights = min(len(insights), 10)
        if num_insights <= 4:
            cols = 1
            card_width = 80
            card_height = 12
            start_x = 10
        elif num_insights <= 6:
            cols = 2
            card_width = 42
            card_height = 11
            start_x = 7
        else:
            cols = 2
            card_width = 42
            card_height = 8
            start_x = 7
        
        start_y = 75
        gap = 3
        
        accent_colors = [self.colors['accent2'], self.colors['accent3'], 
                        self.colors['accent4'], self.colors['primary'],
                        self.colors['accent']]
        
        for i, insight in enumerate(insights[:num_insights]):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (card_width + gap)
            y = start_y - row * (card_height + gap)
            
            # Modern card with glow effect
            accent = accent_colors[i % len(accent_colors)]
            
            # Glow layers
            for offset in range(3, 0, -1):
                glow = FancyBboxPatch((x - offset*0.3, y - card_height - offset*0.3), 
                                     card_width + offset*0.6, card_height + offset*0.6,
                                     boxstyle="round,pad=0.3",
                                     facecolor=accent, alpha=0.05, zorder=2)
                ax.add_patch(glow)
            
            # Main card
            card = FancyBboxPatch((x, y - card_height), card_width, card_height,
                                 boxstyle="round,pad=0.4",
                                 facecolor=self.colors['gradient2'],
                                 edgecolor=accent,
                                 linewidth=3, alpha=0.95, zorder=3)
            ax.add_patch(card)
            
            # Accent stripe at top
            stripe = Rectangle((x + 2, y - 2), card_width - 4, 1.5,
                             facecolor=accent, alpha=0.9, zorder=4)
            ax.add_patch(stripe)
            
            # Text with smart font sizing
            text_fontsize = 16 if card_height > 10 else 14 if card_height > 8 else 12
            ax.text(x + card_width/2, y - card_height/2, insight, 
                   ha='center', va='center', 
                   fontsize=text_fontsize, fontweight='600', wrap=True,
                   color=self.colors['text'], zorder=5)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '06_insights.png'), 
                    dpi=150, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()
        print("✓ Created insights slide")
    
    def generate_all(self):
        """Generate all slides with memory management"""
        print("\n📊 Generating Wrapped presentation...")
        print("-" * 50)
        
        # Generate slides one at a time with garbage collection
        self.create_title_slide()
        gc.collect()
        
        self.create_listening_time_slide()
        gc.collect()
        
        self.create_top_artist_slide()
        gc.collect()
        
        self.create_top_artists_chart()
        gc.collect()
        
        self.create_insights_slide()
        gc.collect()
        
        gallery_count = self.create_show_gallery_slides()
        gc.collect()
        
        self.create_day_of_week_chart()
        gc.collect()
        
        self.create_top_day_slide()
        gc.collect()
        
        self.create_stats_summary_slide()
        gc.collect()
        
        self.create_monthly_timeline()
        gc.collect()
        
        self.create_finale_slide()
        gc.collect()
        
        # Renumber files to maintain order
        import shutil
        file_mapping = {
            '04_top_artists_chart.png': '04_top_artists.png',
            '07_day_of_week.png': '07_day_of_week.png',
            '08_top_day.png': '08_top_day.png',
            '09_summary_stats.png': '09_summary_stats.png',
            '10_monthly_timeline.png': '10_monthly_timeline.png',
            '11_finale.png': '11_finale.png'
        }
        for old_name, new_name in file_mapping.items():
            old_path = os.path.join(self.output_dir, old_name)
            new_path = os.path.join(self.output_dir, new_name)
            if os.path.exists(old_path) and old_name != new_name:
                if os.path.exists(new_path):
                    os.remove(new_path)
                shutil.move(old_path, new_path)
        
        print("-" * 50)
        print(f"✅ All slides saved to '{self.output_dir}' folder!")
        print("\nYour Archive.org Wrapped presentation is ready! 🎉")

def main():
    print("Loading data...")
    analyzer = ListeningHistoryAnalyzer()
    analyzer.load_data()
    
    print("\nCreating presentation...")
    presentation = WrappedPresentation(analyzer)
    presentation.generate_all()

if __name__ == '__main__':
    main()
