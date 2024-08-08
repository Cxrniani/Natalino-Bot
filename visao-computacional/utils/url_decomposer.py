from urllib.parse import urlparse

def url_decomposer_s3bucket(url):
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Extract bucket name from the netloc
    bucket_name = parsed_url.netloc.split('.')[0]
       
    # Extract image name from the path (excluding file extension)
    id_image = parsed_url.path.split('/')[-1].split('.')[0]

    # Extract format from the path (file extension)
    format_image = parsed_url.path.split('.')[-1]
    
    return bucket_name, id_image, format_image

def url_decomposer(url):
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Extract the path without the format (file extension)
    path_parts = parsed_url.path.split('.')
    format_image = path_parts[-1]
    url_without_format = url.replace(f'.{format_image}', '')
    
    return url_without_format, format_image