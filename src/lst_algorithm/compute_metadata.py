import ee

def add_timestamp(image):
    timestamp = image.getNumber('system:time_start').toFloat()
    return image.addBands(ee.Image.constant(timestamp).rename('TIMESTAMP'))
    # # Convert the system:time_start property to a human-readable string
    # timestamp_string = ee.Date(image.get("system:time_start")).format(
    #     "YYYY-MM-DD HH:mm:ss"
    # )
    # # Set the timestamp string as a new property on the image
    # return image.set("timestamp", timestamp_string)

def add_index_func(date_start):
    def add_index(image):
        image_date = image.date()
        image_ind = image_date.difference(date_start, 'day').toInt()
        image = image.set('INDEX', image_ind)
        return image
    return add_index
