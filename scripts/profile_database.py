"""Database profiling script for storage optimization analysis."""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def profile_database():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5433/pawarisk')

    async with engine.connect() as conn:
        # 1. Table sizes with TOAST
        print('=== TABLE SIZES ===')
        r = await conn.execute(text('''
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) as table_size,
                pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_total_relation_size(schemaname||'.'||tablename) as total_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        '''))
        table_sizes = r.fetchall()
        for row in table_sizes:
            print(f'{row[1]}: {row[4]} (table: {row[2]}, index: {row[3]})')

        # Calculate total
        total_bytes = sum([row[5] for row in table_sizes])
        print(f'\nTOTAL: {total_bytes / (1024**3):.2f} GB')

        # 2. Row counts (approximate via pg_class for speed)
        print('\n=== ROW COUNTS (approximate) ===')
        r = await conn.execute(text('''
            SELECT relname, reltuples::bigint
            FROM pg_class
            WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            AND relkind = 'r'
            ORDER BY reltuples DESC
        '''))
        for row in r.fetchall():
            if row[1] > 0:
                print(f'{row[0]}: {row[1]:,}')

        # 3. Exact counts for key tables
        print('\n=== EXACT COUNTS (key tables) ===')
        for table in ['odds_snapshots', 'market_odds', 'competitor_odds_snapshots', 'competitor_market_odds', 'scrape_runs', 'scrape_errors', 'scrape_phase_logs', 'scrape_batches']:
            try:
                r = await conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count = r.scalar()
                print(f'{table}: {count:,}')
            except Exception as e:
                print(f'{table}: ERROR - {e}')

        # 4. JSON column size estimates
        print('\n=== JSON COLUMN ESTIMATES ===')

        # raw_response in odds_snapshots
        try:
            r = await conn.execute(text('''
                SELECT
                    pg_size_pretty(SUM(pg_column_size(raw_response))::bigint) as estimated_size,
                    COUNT(*) as total_rows,
                    COUNT(raw_response) as non_null_rows,
                    SUM(pg_column_size(raw_response))::bigint as raw_bytes
                FROM odds_snapshots
            '''))
            row = r.fetchone()
            print(f'odds_snapshots.raw_response: {row[0]} ({row[2]:,} non-null of {row[1]:,} total) [{row[3]} bytes]')
        except Exception as e:
            print(f'odds_snapshots.raw_response: {e}')

        # raw_response in competitor_odds_snapshots
        try:
            r = await conn.execute(text('''
                SELECT
                    pg_size_pretty(SUM(pg_column_size(raw_response))::bigint) as estimated_size,
                    COUNT(*) as total_rows,
                    COUNT(raw_response) as non_null_rows,
                    SUM(pg_column_size(raw_response))::bigint as raw_bytes
                FROM competitor_odds_snapshots
            '''))
            row = r.fetchone()
            print(f'competitor_odds_snapshots.raw_response: {row[0]} ({row[2]:,} non-null of {row[1]:,} total) [{row[3]} bytes]')
        except Exception as e:
            print(f'competitor_odds_snapshots.raw_response: {e}')

        # outcomes in market_odds
        try:
            r = await conn.execute(text('''
                SELECT
                    pg_size_pretty(SUM(pg_column_size(outcomes))::bigint) as estimated_size,
                    COUNT(*) as rows,
                    SUM(pg_column_size(outcomes))::bigint as raw_bytes
                FROM market_odds
            '''))
            row = r.fetchone()
            print(f'market_odds.outcomes: {row[0]} ({row[1]:,} rows) [{row[2]} bytes]')
        except Exception as e:
            print(f'market_odds.outcomes: {e}')

        # outcomes in competitor_market_odds
        try:
            r = await conn.execute(text('''
                SELECT
                    pg_size_pretty(SUM(pg_column_size(outcomes))::bigint) as estimated_size,
                    COUNT(*) as rows,
                    SUM(pg_column_size(outcomes))::bigint as raw_bytes
                FROM competitor_market_odds
            '''))
            row = r.fetchone()
            print(f'competitor_market_odds.outcomes: {row[0]} ({row[1]:,} rows) [{row[2]} bytes]')
        except Exception as e:
            print(f'competitor_market_odds.outcomes: {e}')

        # 5. Growth by date (last 7 days)
        print('\n=== GROWTH BY DATE (last 7 days) ===')
        try:
            r = await conn.execute(text('''
                SELECT DATE(captured_at) as date, COUNT(*) as snapshot_count
                FROM odds_snapshots
                WHERE captured_at > NOW() - INTERVAL '7 days'
                GROUP BY DATE(captured_at)
                ORDER BY date
            '''))
            for row in r.fetchall():
                print(f'{row[0]}: {row[1]:,} snapshots')
        except Exception as e:
            print(f'Error: {e}')

        # 6. Retention analysis
        print('\n=== RETENTION ANALYSIS ===')
        try:
            r = await conn.execute(text('''
                SELECT
                    (SELECT COUNT(*) FROM odds_snapshots WHERE captured_at > NOW() - INTERVAL '7 days') as bp7_snapshots,
                    (SELECT COUNT(*) FROM market_odds mo JOIN odds_snapshots os ON mo.snapshot_id = os.id WHERE os.captured_at > NOW() - INTERVAL '7 days') as bp7_markets,
                    (SELECT COUNT(*) FROM competitor_odds_snapshots WHERE captured_at > NOW() - INTERVAL '7 days') as comp7_snapshots,
                    (SELECT COUNT(*) FROM competitor_market_odds cmo JOIN competitor_odds_snapshots cos ON cmo.snapshot_id = cos.id WHERE cos.captured_at > NOW() - INTERVAL '7 days') as comp7_markets
            '''))
            row = r.fetchone()
            print(f'Last 7 days: {row[0]:,} BP snapshots, {row[1]:,} BP markets, {row[2]:,} comp snapshots, {row[3]:,} comp markets')
        except Exception as e:
            print(f'Error (7 days): {e}')

        try:
            r = await conn.execute(text('''
                SELECT
                    (SELECT COUNT(*) FROM odds_snapshots) as bp_total_snapshots,
                    (SELECT COUNT(*) FROM market_odds) as bp_total_markets,
                    (SELECT COUNT(*) FROM competitor_odds_snapshots) as comp_total_snapshots,
                    (SELECT COUNT(*) FROM competitor_market_odds) as comp_total_markets
            '''))
            row = r.fetchone()
            print(f'ALL TIME: {row[0]:,} BP snapshots, {row[1]:,} BP markets, {row[2]:,} comp snapshots, {row[3]:,} comp markets')
        except Exception as e:
            print(f'Error (all): {e}')

        # 7. Data vs Index ratio
        print('\n=== DATA VS INDEX BREAKDOWN ===')
        try:
            r = await conn.execute(text('''
                SELECT
                    pg_size_pretty(SUM(pg_table_size(schemaname||'.'||tablename))::bigint) as total_data,
                    pg_size_pretty(SUM(pg_indexes_size(schemaname||'.'||tablename))::bigint) as total_indexes,
                    SUM(pg_table_size(schemaname||'.'||tablename))::bigint as data_bytes,
                    SUM(pg_indexes_size(schemaname||'.'||tablename))::bigint as index_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
            '''))
            row = r.fetchone()
            total = row[2] + row[3]
            data_pct = (row[2] / total) * 100 if total > 0 else 0
            index_pct = (row[3] / total) * 100 if total > 0 else 0
            print(f'Data: {row[0]} ({data_pct:.1f}%)')
            print(f'Indexes: {row[1]} ({index_pct:.1f}%)')
        except Exception as e:
            print(f'Error: {e}')

        # 8. Oldest data
        print('\n=== DATA AGE RANGE ===')
        try:
            r = await conn.execute(text('''
                SELECT
                    MIN(captured_at) as oldest,
                    MAX(captured_at) as newest,
                    NOW() - MIN(captured_at) as age
                FROM odds_snapshots
            '''))
            row = r.fetchone()
            print(f'Oldest: {row[0]}')
            print(f'Newest: {row[1]}')
            print(f'Data span: {row[2]}')
        except Exception as e:
            print(f'Error: {e}')

        # 9. Top tables breakdown
        print('\n=== TOP 5 TABLES BY SIZE ===')
        for i, row in enumerate(table_sizes[:5]):
            pct = (row[5] / total_bytes) * 100 if total_bytes > 0 else 0
            print(f'{i+1}. {row[1]}: {row[4]} ({pct:.1f}%)')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(profile_database())
