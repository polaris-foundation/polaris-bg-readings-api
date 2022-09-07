import codecs
import subprocess

import sadisplay

from gdm_bg_readings_api.models import (
    amber_alert,
    dose,
    hba1c_reading,
    hba1c_target,
    patient,
    patient_alert,
    prandial_tag,
    reading,
    reading_banding,
    reading_metadata,
    red_alert,
)

desc = sadisplay.describe(
    [
        amber_alert.AmberAlert,
        dose.Dose,
        hba1c_reading.Hba1cReading,
        hba1c_target.Hba1cTarget,
        patient.Patient,
        patient_alert.PatientAlert,
        prandial_tag.PrandialTag,
        reading.Reading,
        reading_banding.ReadingBanding,
        reading_metadata.ReadingMetadata,
        red_alert.RedAlert,
    ]
)
with codecs.open("docs/schema.plantuml", "w", encoding="utf-8") as f:
    f.write(sadisplay.plantuml(desc).rstrip() + "\n")

with codecs.open("docs/schema.dot", "w", encoding="utf-8") as f:
    f.write(sadisplay.dot(desc).rstrip() + "\n")

my_cmd = ["dot", "-Tpng", "docs/schema.dot"]
with open("docs/schema.png", "w") as outfile:
    subprocess.run(my_cmd, stdout=outfile)
