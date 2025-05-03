import asyncio

from pagefind.index import IndexConfig, PagefindIndex


async def index_site(site=None, output_path=None, logfile=None):
    """Index a site using Pagefind.

    Args:
    site : str, optional
        Path to the site directory to index.
    output_path : str, optional
        Path where the index should be output.
    logfile : str, optional
        Path to the log file.

    """
    config = IndexConfig(logfile=logfile, output_path=output_path, verbose=True)
    async with PagefindIndex(config=config) as index:
        await asyncio.gather(
            index.add_directory(site),
        )

        await index.get_files()


if __name__ == "__main__":
    asyncio.run(index_site())
