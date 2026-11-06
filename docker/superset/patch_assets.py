"""Ajustes mínimos sobre los assets de Superset 3.1.1.

1. Habilita el filtro cruzado en los mapas deck.gl y hace que el clic emita
   el nombre de la provincia (no la geometría ni el arreglo acumulado).
2. Marca deck.gl Polygon como interactivo (compatibilidad con el mapa previo).
3. Deshabilita el zoom/desplazamiento del mapa para la presentación.
4. Habilita el clic en el mapa GeoJSON combinado (provincias + sucursales).

El script es idempotente: si los parches ya están aplicados no hace nada.
"""
from pathlib import Path

ASSETS = Path("/app/superset/static/assets")

POLYGON_MARKER = 'name:(0,l.t)("deck.gl Polygon")'
POLYGON_MARKER_PATCHED = POLYGON_MARKER + ',behaviors:["INTERACTIVE_CHART"]'
CLICK_OLD = "p(l),r(s),n.table_filter&&i(n.line_column,d,!1,!0)"
CLICK_NEW = "p(l),r(s),n.table_filter&&i(n.line_column,e,!1,!0)"
TRANSFORM_START = "function fa(e){"
TRANSFORM_END = "function ba("
TRANSFORM_PATCHED = (
    "function fa(e){const{datasource:t,height:o,hooks:r,queriesData:a,"
    "rawFormData:n,width:i,emitCrossFilters:c}=e,"
    "{onAddFilter:l=ha,setControlValue:s=ha,setDataMask:u}=r;"
    "const d=(c&&u)?(e,t)=>{let v=t,col=\"provincia\";"
    "if(\"string\"==typeof v&&0===v.indexOf(\"sucursal:\")){"
    "col=\"nombre_sucursal\";v=v.slice(9);}"
    "else if(\"string\"==typeof v&&0===v.indexOf(\"provincia:\")){"
    "col=\"provincia\";v=v.slice(10);}"
    "return u({extraFormData:{filters:[{col:col,op:\"IN\",val:[v]}]},"
    "filterState:{label:[v],value:[v],selectedValues:[v]}})}:l;"
    "return{datasource:t,formData:n,height:o,onAddFilter:d,payload:a[0],"
    "setControlValue:s,viewport:{...n.viewport,height:o,width:i},width:i}}"
)


def _js_files():
    return list(ASSETS.glob("*.js"))


def patch_polygon_behavior():
    for path in _js_files():
        text = path.read_text(errors="ignore")
        if POLYGON_MARKER_PATCHED in text:
            return
        if POLYGON_MARKER in text:
            if text.count(POLYGON_MARKER) != 1:
                raise RuntimeError(f"Marcador deck.gl Polygon inesperado en {path}")
            path.write_text(
                text.replace(POLYGON_MARKER, POLYGON_MARKER_PATCHED, 1)
            )
            print(f"[patch-assets] deck.gl Polygon interactivo: {path.name}")
            return
    raise RuntimeError("No se encontró el marcador de deck.gl Polygon")


def patch_polygon_click():
    for path in _js_files():
        text = path.read_text(errors="ignore")
        if "getPolygon:Z" not in text:
            continue
        if CLICK_NEW in text:
            return
        if CLICK_OLD in text:
            path.write_text(text.replace(CLICK_OLD, CLICK_NEW, 1))
            print(f"[patch-assets] clic de polígono corregido: {path.name}")
            return
    raise RuntimeError("No se encontró el manejador de clic de deck.gl Polygon")


def patch_deck_transform():
    for path in _js_files():
        text = path.read_text(errors="ignore")
        start = text.find(TRANSFORM_START)
        if start == -1 or "deck.gl Polygon" not in text:
            continue
        if text.startswith(TRANSFORM_PATCHED, start):
            return
        end = text.find(TRANSFORM_END, start)
        if end == -1:
            raise RuntimeError(f"No se pudo delimitar transformProps en {path}")
        text = text[:start] + TRANSFORM_PATCHED + text[end:]
        path.write_text(text)
        print(f"[patch-assets] filtro cruzado por provincia: {path.name}")
        return
    raise RuntimeError("No se encontró transformProps de deck.gl")


def patch_disable_zoom():
    old = "controller:!0,width:"
    new = "controller:!1,width:"
    patched = 0
    for path in _js_files():
        text = path.read_text(errors="ignore")
        if old in text:
            path.write_text(text.replace(old, new))
            patched += 1
            print(f"[patch-assets] zoom deshabilitado: {path.name}")
    if patched == 0:
        print("[patch-assets] zoom ya deshabilitado")


GEO_CLICK_CALLBACK = 'function(v){return o("provincia",v)}'


def patch_geojson_click():
    # 0321: getLayer `_` recibe onAddFilter como tercer argumento.
    old_component = "y=_(i,a,0,n)"
    new_component = "y=_(i,a,c,n)"
    old_layer = "...(0,c.N)(i,r,v)})}"
    new_layer = (
        "...(0,c.N)(i,r,v,o?" + GEO_CLICK_CALLBACK + ":void 0)})}"
    )
    # 98ec: getLayer `S` recibe onAddFilter como tercer argumento.
    old_component2 = "f=S(i,l,0,a)"
    new_component2 = "f=S(i,l,u,a)"
    old_layer2 = "...(0,u.N)(i,n,x)})}"
    new_layer2 = (
        "...(0,u.N)(i,n,x,o?" + GEO_CLICK_CALLBACK + ":void 0)})}"
    )
    patched = 0
    for path in _js_files():
        text = path.read_text(errors="ignore")
        if "geojson-layer-" not in text:
            continue
        changed = False
        if old_component in text and old_layer in text:
            text = text.replace(old_component, new_component, 1)
            text = text.replace(old_layer, new_layer, 1)
            changed = True
        if old_component2 in text and old_layer2 in text:
            text = text.replace(old_component2, new_component2, 1)
            text = text.replace(old_layer2, new_layer2, 1)
            changed = True
        if changed:
            path.write_text(text)
            patched += 1
            print(f"[patch-assets] clic GeoJSON habilitado: {path.name}")
    if patched == 0:
        print("[patch-assets] clic GeoJSON ya habilitado o no encontrado")


def patch_geojson_pickable():
    # En Superset 3.1.1 pickable dependia de que existiera js_tooltip; sin
    # tooltip el mapa no recibia clics. Se fuerza pickable para el filtro.
    old = "pickable:Boolean(s)"
    new = "pickable:!0"
    patched = 0
    for path in _js_files():
        text = path.read_text(errors="ignore")
        if old in text:
            path.write_text(text.replace(old, new))
            patched += 1
            print(f"[patch-assets] clic en mapa habilitado: {path.name}")
    if patched == 0:
        print("[patch-assets] clic en mapa ya habilitado o no encontrado")


def main():
    patch_polygon_behavior()
    patch_polygon_click()
    patch_deck_transform()
    patch_disable_zoom()
    patch_geojson_click()
    patch_geojson_pickable()


if __name__ == "__main__":
    main()
