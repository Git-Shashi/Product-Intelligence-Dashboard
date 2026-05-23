from app.services.competitor.mock_competitor import MockCompetitorService

# Default: always use mock. Real scraping/API would slot in here behind the same interface.
_service = MockCompetitorService()


def get_competitor_service() -> MockCompetitorService:
    return _service
