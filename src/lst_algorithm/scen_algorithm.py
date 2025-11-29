from .constants import L8B10_COEFFICIENTS, BOLTZMANN_CONSTANT
import ee


def compute_AFs(tpw: ee.Image, month: int, latitude: float) -> ee.Image:
    constant_one = tpw.multiply(0).add(1)
    squared = tpw.multiply(tpw)
    water_bands = ee.Image.cat([squared, tpw, constant_one])
    result_images = {}
    for key, value in L8B10_COEFFICIENTS.items():
        result_images[key] = (water_bands
                                .multiply(ee.Image.constant(value))
                                .reduce(ee.Reducer.sum())
                                .rename(key))
    rl = abs(latitude) / 90
    rt = abs(month - 7) / 6 # summer is 7 at northern hemisphere
    phi = (result_images["PHI_B"]
        .add(result_images["PHI_Dl"].multiply(rl))
        .add(result_images["PHI_Dt"].multiply(rt)).rename('PHI'))

    result = ee.Image.cat([result_images["TAU"], result_images["PSI"], phi])
    return result

def compute_radiances(afs: ee.Image, elv: ee.Image) -> ee.Image:
    phi = afs.select('PHI')
    psi = afs.select('PSI')
    tau = afs.select('TAU')

    air_upstream = phi.rename('air_upstream')
    air_downstream = (psi.multiply(phi)
                      .divide(tau)
                      .rename('air_downstream'))

    tau_sw = elv.multiply(2e-5).add(0.75)

    result = ee.Image.cat([
        air_upstream,
        air_downstream,
        tau_sw,
    ])

    return result

def compute_air_temperature(radiances: ee.Image) -> ee.Image:
    air_downstream = radiances.select('air_downstream')
    air_emissivity = (radiances.select('tau_sw').log()
                      .multiply(-1)
                      .pow(0.99)
                      .multiply(0.85)
                      .rename('air_emissivity'))
    air_temperature = (air_downstream
                      .divide(air_emissivity)
                      .divide(BOLTZMANN_CONSTANT)
                      .pow(0.25).rename('air_temperature'))
    return air_temperature

def add_airt_band(landsat, image, month, latitude):
    """
    Apply the SCEN algorithm to compute the LST.
    """
    if landsat != "L8":
        return 
    tpw = image.select("TPW")
    elv = image.select("ELEVATION")
    afs = compute_AFs(tpw, month, latitude)
    radiances = compute_radiances(afs, elv)
    air_temperature = compute_air_temperature(radiances)

    image = image.addBands(air_temperature.rename("AIRT"))
    image = image.addBands(radiances.select('air_upstream').rename("AIR_UPSTREAM"))
    image = image.addBands(radiances.select('air_downstream').rename("AIR_DOWNSTREAM"))
    image = image.addBands(radiances.select('tau_sw').rename("TAU_SW"))
    return image
