#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruye las presentaciones de defensa y estudio con la plantilla UCE."""

from __future__ import annotations

from build_defensa import build_defensa
from pres_common import BASE, load_data, make_charts, prepare_template


def main():
    data = load_data()
    charts = make_charts(data)
    title_bg, assets = prepare_template()
    charts.update(assets)

    defensa = build_defensa(data, charts, title_bg)
    defensa.save(BASE / "Presentacion_Defensa_Complexivo_UCE.pptx")
    print("Defensa: %d diapositivas" % len(defensa.slides))

    # La presentación de estudio se incorpora en el siguiente bloque.
    from build_estudio import build_estudio

    estudio = build_estudio(data, charts, title_bg)
    estudio.save(BASE / "Presentacion_Estudio_Complexivo_UCE.pptx")
    print("Estudio: %d diapositivas" % len(estudio.slides))


if __name__ == "__main__":
    main()
