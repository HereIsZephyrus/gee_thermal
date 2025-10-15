def add_evi_band(landsat, image):
    """
    Compute EVI values for a given Landsat image.

    Parameters:
    - landsat (str): ID of the Landsat satellite (e.g., 'L8')
    - image (ee.Image): Input Landsat image

    Returns:
    - ee.Image: Image with added EVI band
    """

    # Choose bands based on the Landsat satellite ID
    if landsat in ["L8", "L9"]:
        nir = "SR_B5"
        red = "SR_B4"
        blue = "SR_B2"
    else:
        nir = "SR_B4"
        red = "SR_B3"
        blue = "SR_B2"

    gain = 2.5
    c1 = 6
    c2 = 7.5
    L = 1

    # Compute EVI
    evi = image.expression(
        f"{gain} * (nir - red) / (nir + {c1} * red - {c2} * blue + {L})",
        {
            "nir": image.select(nir).multiply(0.0000275).add(-0.2),
            "red": image.select(red).multiply(0.0000275).add(-0.2),
            "blue": image.select(blue).multiply(0.0000275).add(-0.2),
        },
    ).rename("EVI")

    return image.addBands(evi)
