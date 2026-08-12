from .models import BrandManifest, BrandVariant, MonthDayWindow

ATLANTICUS_BRAND_MANIFEST = BrandManifest(
    brand_key='atlanticus',
    default_asset_resource='atlanticus-primary.png',
    variants=(
        BrandVariant(
            key='fiestas_patrias',
            display_name='Fiestas Patrias',
            activation_rule=MonthDayWindow(9, 1, 9, 30),
        ),
        BrandVariant(
            key='halloween',
            display_name='Halloween',
            activation_rule=MonthDayWindow(10, 25, 10, 31),
        ),
        BrandVariant(
            key='christmas',
            display_name='Navidad',
            activation_rule=MonthDayWindow(12, 1, 12, 25),
        ),
        BrandVariant(
            key='new_year',
            display_name='Año Nuevo',
            activation_rule=MonthDayWindow(12, 26, 1, 2),
        ),
    ),
)
