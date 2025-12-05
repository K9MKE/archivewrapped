"""
Archive.org Listening History Analyzer
Analyzes listening history data and generates statistics
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os

class ListeningHistoryAnalyzer:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.summary_df = None
        self.favorites_df = None
        self.detailed_data = None
        
    def load_data(self):
        """Load all data files"""
        print("Loading data files...")
        
        # Load summary TSV
        summary_path = os.path.join(self.data_dir, 'ListeningHistorySummary.tsv')
        self.summary_df = pd.read_csv(summary_path, sep='\t')
        self.summary_df['listenedOn'] = pd.to_datetime(self.summary_df['listenedOn'])
        
        # Filter to 2025 only
        self.summary_df = self.summary_df[self.summary_df['listenedOn'].dt.year == 2025]
        
        # Load favorites TSV
        favorites_path = os.path.join(self.data_dir, 'Favorites.tsv')
        self.favorites_df = pd.read_csv(favorites_path, sep='\t')
        self.favorites_df['dateAdded'] = pd.to_datetime(self.favorites_df['dateAdded'])
        
        # Filter favorites to 2025 only
        self.favorites_df = self.favorites_df[self.favorites_df['dateAdded'].dt.year == 2025]
        
        # Load detailed JSON
        detailed_path = os.path.join(self.data_dir, 'DetailedListeningHistory.json')
        with open(detailed_path, 'r', encoding='utf-8') as f:
            self.detailed_data = json.load(f)
        
        print(f"Loaded {len(self.summary_df)} listening sessions")
        print(f"Loaded {len(self.favorites_df)} favorites")
        print(f"Loaded detailed data for {len(self.detailed_data.get('artists', []))} artists")
        
    def calculate_total_minutes(self):
        """Calculate total minutes listened"""
        # Calculate actual listening time (duration * percentListenedTo)
        total_seconds = (self.summary_df['duration'] * self.summary_df['percentListenedTo']).sum()
        total_minutes = total_seconds / 60
        total_hours = total_minutes / 60
        
        return {
            'total_minutes': round(total_minutes, 2),
            'total_hours': round(total_hours, 2),
            'total_days': round(total_hours / 24, 2)
        }
    
    def get_total_listening_time(self):
        """Alias for calculate_total_minutes for compatibility"""
        return self.calculate_total_minutes()
    
    def get_top_artists(self, n=10):
        """Get top N artists by listening time"""
        artist_time = self.summary_df.groupby('artistName').agg({
            'duration': lambda x: (x * self.summary_df.loc[x.index, 'percentListenedTo']).sum(),
            'recordingIdentifier': 'count'
        }).reset_index()
        
        artist_time.columns = ['artistName', 'total_seconds', 'session_count']
        artist_time['total_minutes'] = artist_time['total_seconds'] / 60
        artist_time['total_hours'] = artist_time['total_minutes'] / 60
        artist_time = artist_time.sort_values('total_seconds', ascending=False).head(n)
        
        return artist_time
    
    def get_listening_by_day(self):
        """Get listening statistics by day of week"""
        self.summary_df['day_of_week'] = self.summary_df['listenedOn'].dt.day_name()
        self.summary_df['listening_time'] = self.summary_df['duration'] * self.summary_df['percentListenedTo']
        
        day_stats = self.summary_df.groupby('day_of_week').agg({
            'listening_time': 'sum',
            'recordingIdentifier': 'count'
        }).reset_index()
        
        day_stats.columns = ['day', 'total_seconds', 'session_count']
        day_stats['total_minutes'] = day_stats['total_seconds'] / 60
        
        # Order by day of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_stats['day'] = pd.Categorical(day_stats['day'], categories=day_order, ordered=True)
        day_stats = day_stats.sort_values('day')
        
        return day_stats
    
    def get_top_listening_days(self, n=10):
        """Get days with the most listening time"""
        self.summary_df['date'] = self.summary_df['listenedOn'].dt.date
        self.summary_df['listening_time'] = self.summary_df['duration'] * self.summary_df['percentListenedTo']
        
        daily_stats = self.summary_df.groupby('date').agg({
            'listening_time': 'sum',
            'recordingIdentifier': 'count'
        }).reset_index()
        
        daily_stats.columns = ['date', 'total_seconds', 'session_count']
        daily_stats['total_minutes'] = daily_stats['total_seconds'] / 60
        daily_stats['total_hours'] = daily_stats['total_minutes'] / 60
        daily_stats = daily_stats.sort_values('total_seconds', ascending=False).head(n)
        
        return daily_stats
    
    def get_favorite_artists(self):
        """Get favorited artists"""
        return self.favorites_df[self.favorites_df['favoriteType'] == 'artist'].sort_values('dateAdded', ascending=False)
    
    def get_favorite_recordings(self):
        """Get favorited recordings"""
        return self.favorites_df[self.favorites_df['favoriteType'] == 'recording'].sort_values('dateAdded', ascending=False)
    
    def get_listening_by_month(self):
        """Get listening statistics by month"""
        self.summary_df['year_month'] = self.summary_df['listenedOn'].dt.to_period('M')
        self.summary_df['listening_time'] = self.summary_df['duration'] * self.summary_df['percentListenedTo']
        
        monthly_stats = self.summary_df.groupby('year_month').agg({
            'listening_time': 'sum',
            'recordingIdentifier': 'count'
        }).reset_index()
        
        monthly_stats.columns = ['month', 'total_seconds', 'session_count']
        monthly_stats['total_minutes'] = monthly_stats['total_seconds'] / 60
        monthly_stats['total_hours'] = monthly_stats['total_minutes'] / 60
        monthly_stats['month'] = monthly_stats['month'].astype(str)
        
        return monthly_stats
    
    def get_top_shows(self, n=10):
        """Get top shows by listening time"""
        # Combine artist, date, and venue to identify unique shows
        self.summary_df['show_id'] = (self.summary_df['artistName'] + ' - ' + 
                                       self.summary_df['showDate'] + ' @ ' + 
                                       self.summary_df['venue'])
        self.summary_df['listening_time'] = self.summary_df['duration'] * self.summary_df['percentListenedTo']
        
        show_stats = self.summary_df.groupby(['show_id', 'artistName', 'showDate', 'venue', 'location', 'recordingIdentifier']).agg({
            'listening_time': 'sum',
            'sessionIdentifier': 'count'
        }).reset_index()
        
        show_stats.columns = ['show_id', 'artist', 'date', 'venue', 'location', 'recording_id', 'total_seconds', 'listen_count']
        show_stats['total_minutes'] = show_stats['total_seconds'] / 60
        show_stats['total_hours'] = show_stats['total_minutes'] / 60
        show_stats = show_stats.sort_values('total_seconds', ascending=False).head(n)
        
        return show_stats
    
    def get_personalized_insights(self):
        """Extract personalized insights and interesting patterns from listening data"""
        insights = []
        
        # Calculate listening streaks
        self.summary_df['date'] = self.summary_df['listenedOn'].dt.date
        dates = sorted(self.summary_df['date'].unique())
        if len(dates) > 1:
            max_streak = 1
            current_streak = 1
            for i in range(1, len(dates)):
                if (dates[i] - dates[i-1]).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            if max_streak > 2:
                insights.append(f"{max_streak}-day listening streak")
        
        # Find favorite time of day
        self.summary_df['hour'] = self.summary_df['listenedOn'].dt.hour
        hour_counts = self.summary_df['hour'].value_counts()
        if len(hour_counts) > 0:
            favorite_hour = hour_counts.index[0]
            if 5 <= favorite_hour < 12:
                insights.append(f"Morning listener (peak at {favorite_hour}:00)")
            elif 12 <= favorite_hour < 17:
                insights.append(f"Afternoon vibes (peak at {favorite_hour}:00)")
            elif 17 <= favorite_hour < 21:
                insights.append(f"Evening sessions (peak at {favorite_hour}:00)")
            else:
                insights.append(f"Night owl (peak at {favorite_hour}:00)")
        
        # Weekend vs weekday
        self.summary_df['is_weekend'] = self.summary_df['listenedOn'].dt.dayofweek >= 5
        weekend_pct = (self.summary_df['is_weekend'].sum() / len(self.summary_df)) * 100
        if weekend_pct > 60:
            insights.append(f"Weekend warrior - {weekend_pct:.0f}% on Sat/Sun")
        elif weekend_pct < 30:
            insights.append(f"Weekday listener - {100-weekend_pct:.0f}% Mon-Fri")
        
        # Artist diversity
        unique_artists = self.summary_df['artistName'].nunique()
        total_sessions = len(self.summary_df)
        diversity_ratio = unique_artists / total_sessions
        if diversity_ratio > 0.5:
            insights.append(f"Eclectic taste - {unique_artists} different artists")
        elif diversity_ratio < 0.15:
            top_artist = self.summary_df['artistName'].value_counts().index[0]
            insights.append(f"Superfan of {top_artist}")
        
        # Binge sessions
        self.summary_df['listening_time'] = self.summary_df['duration'] * self.summary_df['percentListenedTo']
        daily_time = self.summary_df.groupby('date')['listening_time'].sum() / 3600
        marathon_days = (daily_time > 4).sum()
        if marathon_days > 0:
            max_day_hours = daily_time.max()
            insights.append(f"{marathon_days} marathon listening days (max {max_day_hours:.1f}h)")
        
        # Month discovery
        self.summary_df['month'] = self.summary_df['listenedOn'].dt.month_name()
        monthly_sessions = self.summary_df['month'].value_counts()
        if len(monthly_sessions) > 0:
            peak_month = monthly_sessions.index[0]
            insights.append(f"Peak listening month: {peak_month}")
        
        # Venue variety
        if 'venue' in self.summary_df.columns:
            unique_venues = self.summary_df['venue'].nunique()
            if unique_venues > 20:
                insights.append(f"Concert explorer - {unique_venues} different venues")
            elif unique_venues < 5:
                fav_venue = self.summary_df['venue'].value_counts().index[0]
                insights.append(f"Loyal to {fav_venue}")
        
        # Time of day consistency
        if len(hour_counts) > 0:
            hour_std = self.summary_df['hour'].std()
            if hour_std < 3:
                insights.append(f"Creature of habit - consistent listening schedule")
            elif hour_std > 6:
                insights.append(f"Free spirit - listening at all hours")
        
        # Discovery rate - new artists over time
        if len(dates) > 30:
            first_half = self.summary_df[self.summary_df['date'] < dates[len(dates)//2]]
            second_half = self.summary_df[self.summary_df['date'] >= dates[len(dates)//2]]
            new_artists = len(set(second_half['artistName']) - set(first_half['artistName']))
            if new_artists > 5:
                insights.append(f"Explorer mode - discovered {new_artists} new artists")
        
        # Show completionist
        completion_rates = self.summary_df['percentListenedTo']
        high_completion = (completion_rates > 0.8).sum()
        completion_pct = (high_completion / len(completion_rates)) * 100
        if completion_pct > 75:
            insights.append(f"Completionist - {completion_pct:.0f}% shows heard fully")
        elif completion_pct < 25:
            insights.append(f"Sampler - explores {100-completion_pct:.0f}% partial shows")
        
        # Longest single session
        max_duration = self.summary_df['duration'].max()
        if max_duration > 7200:  # 2+ hours
            insights.append(f"Epic session - {max_duration/3600:.1f}h longest show")
        
        # Variety within top artist
        if diversity_ratio < 0.15:
            top_artist = self.summary_df['artistName'].value_counts().index[0]
            top_artist_shows = self.summary_df[self.summary_df['artistName'] == top_artist]
            unique_shows = len(top_artist_shows.groupby(['showDate', 'venue']))
            if unique_shows > 10:
                insights.append(f"Deep dive - {unique_shows} different {top_artist} shows")
        
        return insights
    
    def get_stats_summary(self):
        """Get overall statistics summary"""
        time_stats = self.calculate_total_minutes()
        
        # Date range
        first_listen = self.summary_df['listenedOn'].min()
        last_listen = self.summary_df['listenedOn'].max()
        
        # Unique artists and shows
        unique_artists = self.summary_df['artistName'].nunique()
        unique_shows = self.summary_df['recordingIdentifier'].nunique()
        
        # Favorite counts
        favorite_artists = len(self.favorites_df[self.favorites_df['favoriteType'] == 'artist'])
        favorite_recordings = len(self.favorites_df[self.favorites_df['favoriteType'] == 'recording'])
        
        return {
            'total_minutes': time_stats['total_minutes'],
            'total_hours': time_stats['total_hours'],
            'total_days': time_stats['total_days'],
            'first_listen': first_listen,
            'last_listen': last_listen,
            'listening_period_days': (last_listen - first_listen).days,
            'unique_artists': unique_artists,
            'unique_shows': unique_shows,
            'total_sessions': len(self.summary_df),
            'favorite_artists_count': favorite_artists,
            'favorite_recordings_count': favorite_recordings
        }

def main():
    analyzer = ListeningHistoryAnalyzer()
    analyzer.load_data()
    
    print("\n" + "="*60)
    print(">>> ARCHIVE.ORG LISTENING HISTORY WRAPPED 2025 <<<")
    print("="*60)
    
    # Overall stats
    stats = analyzer.get_stats_summary()
    print(f"\n📊 OVERALL STATISTICS")
    print(f"   Total Listening Time: {stats['total_hours']:,.1f} hours ({stats['total_days']:.1f} days)")
    print(f"   Time Period: {stats['first_listen'].strftime('%Y-%m-%d')} to {stats['last_listen'].strftime('%Y-%m-%d')}")
    print(f"   Listening Period: {stats['listening_period_days']} days")
    print(f"   Unique Artists: {stats['unique_artists']}")
    print(f"   Unique Shows: {stats['unique_shows']}")
    print(f"   Total Sessions: {stats['total_sessions']}")
    print(f"   Favorite Artists: {stats['favorite_artists_count']}")
    print(f"   Favorite Recordings: {stats['favorite_recordings_count']}")
    
    # Top artists
    print(f"\n🎵 TOP 10 ARTISTS")
    top_artists = analyzer.get_top_artists(10)
    for idx, row in top_artists.iterrows():
        print(f"   {row['artistName']}")
        print(f"      {row['total_hours']:.1f} hours · {row['session_count']} sessions")
    
    # Top shows
    print(f"\n🎸 TOP 10 SHOWS")
    top_shows = analyzer.get_top_shows(10)
    for idx, row in top_shows.iterrows():
        print(f"   {row['artist']} - {row['date']}")
        print(f"      {row['venue']} · {row['total_hours']:.1f} hours · {row['listen_count']} listens")
    
    # Top listening days
    print(f"\n📅 TOP 10 LISTENING DAYS")
    top_days = analyzer.get_top_listening_days(10)
    for idx, row in top_days.iterrows():
        print(f"   {row['date']}")
        print(f"      {row['total_hours']:.1f} hours · {row['session_count']} sessions")
    
    # Listening by day of week
    print(f"\n📆 LISTENING BY DAY OF WEEK")
    day_stats = analyzer.get_listening_by_day()
    for idx, row in day_stats.iterrows():
        print(f"   {row['day']}: {row['total_minutes']:.0f} minutes ({row['session_count']} sessions)")
    
    # Favorite artists
    print(f"\n⭐ FAVORITE ARTISTS")
    fav_artists = analyzer.get_favorite_artists()
    for idx, row in fav_artists.iterrows():
        print(f"   {row['favoriteIdentifier']} (added {row['dateAdded'].strftime('%Y-%m-%d')})")

if __name__ == '__main__':
    main()
