def add_green_band(landsat, image):
    """
    Compute Green values for a given Landsat image.

    Parameters:
    - landsat (str): ID of the Landsat satellite (e.g., 'L8')
    - image (ee.Image): Input Landsat image

    Returns:
    - ee.Image: Image with added Green band
    """

    # Choose bands based on the Landsat satellite ID
    if landsat in ["L8", "L9"]:
        green = "SR_B3"
        red = "SR_B4"
        blue = "SR_B2"
    else:
        green = "SR_B3"
        red = "SR_B4"
        blue = "SR_B2"

    # Compute Green
    green = image.expression(
        "(2 * green - red - blue) / (2 * green + red + blue)",
        {
            "green": image.select(green).multiply(0.0000275).add(-0.2),
            "red": image.select(red).multiply(0.0000275).add(-0.2),
            "blue": image.select(blue).multiply(0.0000275).add(-0.2),
        },
    ).rename("Green")

    return image.addBands(green)
