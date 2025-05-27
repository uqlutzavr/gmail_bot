from gmail_flow import Gmail
import logging
import time

logger = logging.getLogger(__name__)


def main():
    try:
        logger.info("Starting Gmail Bot")
        bot = Gmail()
        bot.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        logger.info("Attempting to restart in 60 seconds...")
        time.sleep(60)
        main()


if __name__ == "__main__":
    main()
