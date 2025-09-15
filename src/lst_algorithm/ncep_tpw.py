import ee


def add_tpw_band(image):
    """
    Add total precipitable water values and index for
    the LUT of SMW algorithm coefficients to the image.

    Parameters:
    - image (ee.Image): Image for which to interpolate the TPW data.
      Needs the 'system:time_start' image property.

    Returns:
    - ee.Image: Image with added 'TPW' and 'TPWpos' bands.
    """
    date = image.date()
    date1 = date
    date2 = date1.advance(3, 'day')

    def datedist(img):
        return img.set(
            "DateDist",
            ee.Number(img.date().millis()).subtract(date.millis()).abs(),
        )

    tpw_collection = (
        ee.ImageCollection("NCEP_RE/surface_wv")
        .filterDate(date1, date2)
        .map(datedist)
    )

    closest = tpw_collection.sort("DateDist").toList(2)

    tpw1 = (
        ee.Image(closest.get(0)).select("pr_wtr")
        if closest.size()
        else ee.Image.constant(-999.0)
    )
    tpw2 = (
    ee.Image(closest.get(1)).select("pr_wtr")
        if ee.Number(closest.size()).gt(1)
        else tpw1
    )

    time1 = (
        ee.Number(tpw1.get("DateDist")).divide(21600000)
        if ee.Number(closest.size()).gt(0)
        else ee.Number(1.0)
    )
    time2 = (
        ee.Number(tpw2.get("DateDist")).divide(21600000)
            if ee.Number(closest.size()).gt(1)
            else ee.Number(0.0)
        )

    tpw = tpw1.expression(
        "tpw1*time2+tpw2*time1",
        {"tpw1": tpw1, "time1": time1, "tpw2": tpw2, "time2": time2},
    ).clip(image.geometry())

    pos = tpw.expression(
        "value = (TPW>0 && TPW<=6) ? 0"
        + ": (TPW>6 && TPW<=12) ? 1"
        + ": (TPW>12 && TPW<=18) ? 2"
        + ": (TPW>18 && TPW<=24) ? 3"
        + ": (TPW>24 && TPW<=30) ? 4"
        + ": (TPW>30 && TPW<=36) ? 5"
        + ": (TPW>36 && TPW<=42) ? 6"
        + ": (TPW>42 && TPW<=48) ? 7"
        + ": (TPW>48 && TPW<=54) ? 8"
        + ": (TPW>54) ? 9"
        + ": 0",
        {"TPW": tpw},
    ).clip(image.geometry())

    withTPW = image.addBands(tpw.rename("TPW")).addBands(pos.rename("TPWpos"))

    return withTPW
