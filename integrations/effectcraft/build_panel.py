"""Build one self-contained UTF-8 JSX, including all translation catalogs."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANGUAGES = ('en', 'cs', 'de', 'es', 'fr', 'pt-br', 'ru', 'uk', 'ka', 'ja', 'zh-hans', 'zh-hant')


def catalogs():
    result = {code: json.loads((HERE/'locales'/f'{code}.json').read_text(encoding='utf-8')) for code in LANGUAGES}
    for code, rows in result.items():
        if rows.keys() != result['en'].keys():
            raise ValueError(f'Incomplete catalog: {code}')
    return result


def build_panel():
    return ('// Generated self-contained panel; edit source catalogs, then reinstall.\n'
            'var CORRIDORKEY_CATALOGS = '+json.dumps(catalogs(), ensure_ascii=True)+';\n'+
            (HERE/'i18n.js').read_text(encoding='utf-8')+'\n'+
            (HERE/'CorridorKey.jsx').read_text(encoding='utf-8'))


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.write_text(build_panel(),encoding='utf-8')
