from src.endpoints import app
from src.utils import logger, config

if __name__ == '__main__':
    app.run(host=config['APP_HOST'], debug=True, threaded=True, port=config['APP_PORT'])
    logger.info(f'API v1.0 online: http://{config['APP_HOST']}:{config['APP_PORT']}')