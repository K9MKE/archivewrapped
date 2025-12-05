from analyze import ListeningHistoryAnalyzer

a = ListeningHistoryAnalyzer('data')
a.load_data()
insights = a.get_personalized_insights()

print(f'Found {len(insights)} personalized insights:')
for insight in insights:
    print(f'  {insight}')
