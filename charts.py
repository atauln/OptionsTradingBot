from img2table.document import Image
from img2table.ocr import TesseractOCR
from PIL import Image as PILImage
from classes import Chart as IAChart

amount_per_contract = 3000
acceptable_loss = 0.3

def extract_from_image(image_path):
    ocr = TesseractOCR(lang="eng")
    pil_image = PILImage.open(image_path)
    pil_image = pil_image.resize((pil_image.width * 3, pil_image.height * 3), PILImage.ADAPTIVE)
    pil_image = pil_image.convert('1', dither=PILImage.NONE)
    pil_image.save(f"refined/{image_path}", quality=20, dpi=(1200, 1200))
    image = Image(f"refined/{image_path}")
    return image.extract_tables(borderless_tables=True, ocr=ocr, min_confidence=40)

def print_chart(chart: IAChart):
    content = chart.extracted_table.content
    for (i, col) in content.items():
        print(f"Row {i}: {[ele.value for ele in col]}")

if __name__ == "__main__":
    name = "1_4_2024_CALL_25DTE"
    chart = IAChart(name, extract_from_image(f"charts/{name}.png")[0])
    #print_chart(chart) # debug
    total_values = chart.get_value_with_threading(amount_per_contract, acceptable_loss)
    print(f"Chart Name: {chart.name}")
    print(f"Release Date: {chart.get_release_date()}")
    print(f"Expiration Date: {chart.get_expiration_date()}")
    print(f"Total Cost: ${chart.get_total_cost(amount_per_contract)}")
    print(f"Total Value: ${total_values[0]}")
    print(f"Total Return: {round(((total_values[0] - chart.get_total_cost(amount_per_contract)) / chart.get_total_cost(amount_per_contract)) * 100, 2)}%")
    print(f"Total Value with Stop Limit at {(1 - acceptable_loss) * 100}%: ${total_values[1]}")
    print(f"Total Return with Stop Limit at {(1 - acceptable_loss) * 100}%: {round(((total_values[1] - chart.get_total_cost(amount_per_contract)) / chart.get_total_cost(amount_per_contract)) * 100, 2)}%")