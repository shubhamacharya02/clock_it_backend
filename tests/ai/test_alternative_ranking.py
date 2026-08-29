from app.ai.schemas.alternative_output import RankedAlternativeResponse, RankedAlternativeItem

def test_ranked_alternative_response_schema():
    item = RankedAlternativeItem(
        variant_id="variant_tofu_250g",
        rank=1,
        alternative_reason="Tofu provides a firm texture and high protein, making it an excellent plant-based substitute for paneer."
    )
    assert item.rank == 1
    assert item.variant_id == "variant_tofu_250g"

    response = RankedAlternativeResponse(
        canonical_name="paneer",
        alternatives=[item]
    )
    assert response.canonical_name == "paneer"
    assert len(response.alternatives) == 1
