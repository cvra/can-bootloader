def slice_into_pages(data, page_size):
    """
    Slices data into chunks that are at max page_size big.
    """
    while len(data) > page_size:
        yield data[:page_size]
        data = data[page_size:]
    yield data
