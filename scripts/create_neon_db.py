import asyncio
import asyncpg

# Change this to your Neon connection string but point to the default 'postgres' database
DSN = "postgresql://neondb_owner:npg_DouesGVE9c4P@ep-orange-paper-a1gxf86x-pooler.ap-southeast-1.aws.neon.tech/postgres?sslmode=require&channel_binding=require"
DB_NAME = "neondb"

async def main():
    try:
        conn = await asyncpg.connect(dsn=DSN)
        try:
            await conn.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"Database '{DB_NAME}' created.")
        except asyncpg.DuplicateDatabaseError:
            print(f"Database '{DB_NAME}' already exists.")
        except Exception as e:
            print('CREATE DATABASE failed:', e)
        finally:
            await conn.close()
    except Exception as e:
        print('Connection failed:', e)

if __name__ == '__main__':
    asyncio.run(main())
