from flask import Flask, request, jsonify
from flask_cors import CORS

# Try different import patterns for terabox-downloader
try:
    from terabox_downloader import TeraboxDownloader
    USING_PACKAGE = True
except ImportError:
    try:
        from terabox_downloader.downloader import TeraboxDownloader
        USING_PACKAGE = True
    except ImportError:
        try:
            import terabox_downloader as TeraboxDownloader
            USING_PACKAGE = True
        except ImportError:
            # Fallback to custom implementation
            try:
                from terabox1 import TeraboxFile, TeraboxLink
                TeraboxDownloader = None
                USING_PACKAGE = False
            except ImportError:
                TeraboxDownloader = None
                USING_PACKAGE = False

application = Flask(__name__)
CORS(app)

@app.route('/api/debug', methods=['GET'])
def debug():
    import sys
    import pkg_resources
    
    # Check if terabox-downloader is installed
    try:
        pkg_resources.get_distribution('terabox-downloader')
        package_installed = True
    except pkg_resources.DistributionNotFound:
        package_installed = False
    
    return jsonify({
        'python_version': sys.version,
        'terabox_downloader_available': TeraboxDownloader is not None,
        'package_installed': package_installed,
        'sys_path': sys.path[:3]  # First 3 paths only
    })

@app.route('/api/get-direct-link', methods=['POST'])
def get_direct_link():
    data = request.get_json()
    share_url = data.get('share_url')

    if not share_url:
        return jsonify({'error': 'share_url is required'}), 400

    try:
        # Check if TeraboxDownloader is available
        if TeraboxDownloader is None:
            return jsonify({'error': 'terabox-downloader package not available'}), 500
        
        # Initialize TeraboxDownloader
        downloader = TeraboxDownloader()
        
        # Try different methods that might exist in the package
        result = None
        
        # Method 1: Try get_download_link
        if hasattr(downloader, 'get_download_link'):
            result = downloader.get_download_link(share_url)
        
        # Method 2: Try download method
        elif hasattr(downloader, 'download'):
            result = downloader.download(share_url)
        
        # Method 3: Try get_info method
        elif hasattr(downloader, 'get_info'):
            result = downloader.get_info(share_url)
        
        # Method 4: Try direct call
        else:
            result = downloader(share_url)
        
        # Handle different response formats
        if result:
            if isinstance(result, dict):
                # If result is a dict, look for common keys
                direct_link = result.get('download_link') or result.get('direct_link') or result.get('url') or result.get('link')
                if direct_link:
                    return jsonify({
                        'direct_link': direct_link,
                        'file_info': result
                    }), 200
            elif isinstance(result, str):
                # If result is a string, assume it's the direct link
                return jsonify({
                    'direct_link': result,
                    'file_info': {'url': result}
                }), 200
            elif isinstance(result, list) and len(result) > 0:
                # If result is a list, take the first item
                first_item = result[0]
                if isinstance(first_item, dict):
                    direct_link = first_item.get('download_link') or first_item.get('direct_link') or first_item.get('url')
                    if direct_link:
                        return jsonify({
                            'direct_link': direct_link,
                            'file_info': first_item
                        }), 200
                elif isinstance(first_item, str):
                    return jsonify({
                        'direct_link': first_item,
                        'file_info': {'url': first_item}
                    }), 200
        
        return jsonify({'error': 'Could not retrieve direct link.'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# This block is for local development only and should not be run in production
# if __name__ == '__main__':
#     application.run(debug=True, port=5000)