def add_ndbi_band(landsat, image):
    """
    Compute NDBI values for a given Landsat image.

    Parameters:
    - landsat (str): ID of the Landsat satellite (e.g., 'L8')
    - image (ee.Image): Input Landsat image

    Returns:
    - ee.Image: Image with added NDBI band
    """

    # Choose bands based on the Landsat satellite ID
    if landsat in ["L8", "L9"]:
        nir = "SR_B5"
        mir = "SR_B6"
    else:
        nir = "SR_B4"
        mir = "SR_B5"

    # Compute NDBI
    ndbi = image.expression(
        "(mir - nir) / (mir + nir)",
        {
            "nir": image.select(nir).multiply(0.0000275).add(-0.2),
            "mir": image.select(mir).multiply(0.0000275).add(-0.2),
        },
    ).rename("NDBI")

    return image.addBands(ndbi)
