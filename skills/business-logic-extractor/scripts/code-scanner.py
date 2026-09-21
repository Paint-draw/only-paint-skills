#!/usr/bin/env python3
"""
代码扫描辅助脚本 - 根据关键词定位与目标功能相关的源代码文件。

用途：
    在业务逻辑抽取的"定位相关代码"阶段，快速从大型代码库中筛选出
    可能与目标功能相关的文件，避免人工逐文件翻阅。

用法：
    python code-scanner.py <目录> --keywords 支付,payment,pay --output candidates.json
    python code-scanner.py <目录> -k coupon,优惠券 -o candidates.json --verbose

输出：
    一个 JSON 文件，包含按相关度排序的候选文件列表，每个文件标注：
    - 文件路径
    - 文件类型（前端/后端/配置/测试/文档/数据库）
    - 匹配的关键词及出现次数
    - 文件大小、行数
    - 相关度评分

注意：
    本脚本只是辅助筛选，不能替代人工阅读。脚本输出的文件仍需人工
    逐一阅读确认其是否真正包含目标功能的业务逻辑。
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# ============================================================
# 配置
# ============================================================

# 支持的代码文件扩展名
CODE_EXTENSIONS: Set[str] = {
    # 后端
    '.py', '.java', '.kt', '.scala', '.go', '.rs', '.rb', '.php',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.clj', '.ex', '.exs',
    '.lua', '.r', '.dart',
    # 前端
    '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.mjs', '.cjs',
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.styl',
    # 数据查询
    '.sql', '.graphql', '.gql', '.proto',
    # 配置
    '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.conf',
    '.env', '.properties', '.xml',
    # 文档
    '.md', '.rst', '.txt', '.adoc',
    # 模板
    '.ejs', '.hbs', '.pug', '.jinja', '.j2', '.twig',
    # 数据库迁移
    '.migration', '.seed',
}

# 跳过的目录
SKIP_DIRS: Set[str] = {
    'node_modules', '.git', 'dist', 'build', '.next', '__pycache__',
    '.cache', 'vendor', 'venv', '.venv', 'env', '.env', 'venv',
    'coverage', '.nyc_output', 'target', 'bin', 'obj', '.idea',
    '.vscode', 'out', 'tmp', 'temp', '.gradle', '.mvn', '.terraform',
    'bower_components', 'jspm_packages', '.pnp', '.yarn',
}

# 文件类型识别规则（按路径关键词）
FILE_TYPE_RULES: List[Tuple[str, str]] = [
    # (路径关键词, 类型)
    ('test', '测试'),
    ('spec', '测试'),
    ('__tests__', '测试'),
    ('tests', '测试'),
    ('mock', '测试'),
    ('fixture', '测试'),
    ('migration', '数据库迁移'),
    ('migrations', '数据库迁移'),
    ('schema', '数据库Schema'),
    ('model', '后端-模型'),
    ('entity', '后端-模型'),
    ('entities', '后端-模型'),
    ('controller', '后端-控制器'),
    ('controllers', '后端-控制器'),
    ('handler', '后端-控制器'),
    ('handlers', '后端-控制器'),
    ('service', '后端-服务'),
    ('services', '后端-服务'),
    ('repository', '后端-仓储'),
    ('repositories', '后端-仓储'),
    ('dao', '后端-仓储'),
    ('mapper', '后端-仓储'),
    ('middleware', '后端-中间件'),
    ('interceptor', '后端-拦截器'),
    ('filter', '后端-过滤器'),
    ('route', '后端-路由'),
    ('routes', '后端-路由'),
    ('router', '后端-路由'),
    ('api', 'API'),
    ('dto', '后端-DTO'),
    ('vo', '后端-VO'),
    ('request', '后端-请求'),
    ('response', '后端-响应'),
    ('validator', '后端-校验'),
    ('validation', '后端-校验'),
    ('config', '配置'),
    ('conf', '配置'),
    ('component', '前端-组件'),
    ('components', '前端-组件'),
    ('page', '前端-页面'),
    ('pages', '前端-页面'),
    ('view', '前端-视图'),
    ('views', '前端-视图'),
    ('template', '前端-模板'),
    ('templates', '前端-模板'),
    ('store', '前端-状态'),
    ('stores', '前端-状态'),
    ('state', '前端-状态'),
    ('hook', '前端-Hook'),
    ('hooks', '前端-Hook'),
    ('composable', '前端-Hook'),
    ('composables', '前端-Hook'),
    ('util', '工具'),
    ('utils', '工具'),
    ('helper', '工具'),
    ('helpers', '工具'),
    ('common', '通用'),
    ('shared', '通用'),
    ('lib', '库'),
    ('libs', '库'),
    ('public', '静态资源'),
    ('static', '静态资源'),
    ('assets', '静态资源'),
    ('locale', '国际化'),
    ('locales', '国际化'),
    ('i18n', '国际化'),
    ('lang', '国际化'),
    ('docs', '文档'),
    ('doc', '文档'),
]

# 前端目录关键词
FRONTEND_INDICATORS = {'src', 'frontend', 'client', 'web', 'app', 'pages', 'components', 'views'}
# 后端目录关键词
BACKEND_INDICATORS = {'server', 'backend', 'api', 'service', 'controller', 'model', 'dao', 'repository'}

# 单文件读取上限（字节），避免读取超大文件
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


# ============================================================
# 核心逻辑
# ============================================================

def should_skip_dir(dirname: str) -> bool:
    """判断是否跳过该目录"""
    return dirname in SKIP_DIRS or dirname.startswith('.')


def detect_file_type(filepath: str, extension: str) -> str:
    """根据路径和扩展名推断文件类型"""
    path_lower = filepath.lower().replace('\\', '/')
    parts = path_lower.split('/')

    # 先按路径关键词匹配
    for keyword, file_type in FILE_TYPE_RULES:
        for part in parts:
            if keyword in part:
                return file_type

    # 按扩展名兜底
    if extension in ('.sql',):
        return '数据库'
    if extension in ('.graphql', '.gql'):
        return 'GraphQL'
    if extension in ('.proto',):
        return 'Protobuf'
    if extension in ('.md', '.rst', '.txt', '.adoc'):
        return '文档'
    if extension in ('.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.conf', '.env', '.properties', '.xml'):
        return '配置'
    if extension in ('.html', '.htm', '.css', '.scss', '.sass', '.less', '.styl'):
        return '前端-样式'
    if extension in ('.vue', '.svelte'):
        return '前端-组件'
    if extension in ('.jsx', '.tsx'):
        return '前端-组件'
    if extension in ('.js', '.ts'):
        # 根据所在目录判断前后端
        if any(ind in parts for ind in BACKEND_INDICATORS):
            return '后端-脚本'
        return '前端-脚本'
    if extension == '.py':
        return '后端-Python'
    if extension in ('.java', '.kt', '.scala'):
        return '后端-JVM'
    if extension == '.go':
        return '后端-Go'
    if extension == '.rs':
        return '后端-Rust'
    if extension == '.rb':
        return '后端-Ruby'
    if extension == '.php':
        return '后端-PHP'
    if extension == '.cs':
        return '后端-C#'

    return '其他'


def scan_file_content(filepath: Path, keywords: List[str]) -> Dict[str, int]:
    """扫描文件内容，统计每个关键词出现次数"""
    try:
        size = filepath.stat().st_size
        if size > MAX_FILE_SIZE:
            return {'_oversize': 1}

        # 尝试多种编码
        content = None
        for encoding in ('utf-8', 'gbk', 'latin-1'):
            try:
                content = filepath.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, OSError):
                continue

        if content is None:
            return {'_unreadable': 1}

        counts = {}
        content_lower = content.lower()
        for kw in keywords:
            kw_lower = kw.lower()
            # 使用正则计数，支持中文
            count = len(re.findall(re.escape(kw_lower), content_lower))
            if count > 0:
                counts[kw] = count
        return counts

    except Exception as e:
        return {'_error': 1}


def count_lines(filepath: Path) -> int:
    """统计文件行数"""
    try:
        size = filepath.stat().st_size
        if size > MAX_FILE_SIZE:
            return -1
        for encoding in ('utf-8', 'gbk', 'latin-1'):
            try:
                with filepath.open(encoding=encoding) as f:
                    return sum(1 for _ in f)
            except (UnicodeDecodeError, OSError):
                continue
        return -1
    except Exception:
        return -1


def compute_relevance(keyword_counts: Dict[str, int], filename_matches: List[str]) -> float:
    """计算相关度评分"""
    score = 0.0
    # 文件名匹配权重高
    for kw in filename_matches:
        score += 10.0
    # 内容匹配：取对数避免高频词主导
    for kw, count in keyword_counts.items():
        if kw.startswith('_'):
            continue
        import math
        score += min(math.log1p(count) * 2, 20.0)
    return round(score, 2)


def scan_codebase(root: Path, keywords: List[str], verbose: bool = False) -> List[Dict]:
    """扫描代码库，返回候选文件列表"""
    candidates = []
    total_files = 0
    scanned_files = 0

    for filepath in root.rglob('*'):
        if not filepath.is_file():
            continue

        # 跳过排除目录
        rel_parts = filepath.relative_to(root).parts
        if any(should_skip_dir(part) for part in rel_parts[:-1]):
            continue

        extension = filepath.suffix.lower()
        if extension not in CODE_EXTENSIONS:
            continue

        total_files += 1

        # 文件名匹配
        filename_lower = filepath.name.lower()
        filename_matches = [kw for kw in keywords if kw.lower() in filename_lower]

        # 内容匹配
        content_counts = scan_file_content(filepath, keywords)

        # 过滤：文件名或内容至少匹配一个关键词
        has_match = bool(filename_matches) or any(
            not k.startswith('_') and v > 0 for k, v in content_counts.items()
        )
        if not has_match:
            continue

        scanned_files += 1

        file_type = detect_file_type(str(filepath.relative_to(root)), extension)
        relevance = compute_relevance(content_counts, filename_matches)
        lines = count_lines(filepath)

        candidates.append({
            'path': str(filepath.relative_to(root)),
            'absolute_path': str(filepath),
            'type': file_type,
            'extension': extension,
            'size_bytes': filepath.stat().st_size,
            'lines': lines,
            'filename_matches': filename_matches,
            'keyword_counts': {k: v for k, v in content_counts.items() if not k.startswith('_')},
            'relevance': relevance,
        })

        if verbose and scanned_files % 50 == 0:
            print(f"  已扫描 {scanned_files} 个候选文件...", file=sys.stderr)

    # 按相关度降序排序
    candidates.sort(key=lambda x: x['relevance'], reverse=True)

    if verbose:
        print(f"扫描完成：共 {total_files} 个代码文件，{scanned_files} 个匹配", file=sys.stderr)

    return candidates


def generate_summary(candidates: List[Dict], keywords: List[str]) -> Dict:
    """生成扫描摘要"""
    type_counts = defaultdict(int)
    for c in candidates:
        type_counts[c['type']] += 1

    # 高相关度文件（relevance >= 10）
    high_relevance = [c for c in candidates if c['relevance'] >= 10]
    medium_relevance = [c for c in candidates if 3 <= c['relevance'] < 10]
    low_relevance = [c for c in candidates if c['relevance'] < 3]

    return {
        'keywords': keywords,
        'total_candidates': len(candidates),
        'by_type': dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        'by_relevance': {
            'high (>=10)': len(high_relevance),
            'medium (3-10)': len(medium_relevance),
            'low (<3)': len(low_relevance),
        },
        'recommendation': (
            f"建议优先阅读 {len(high_relevance)} 个高相关度文件，"
            f"然后按需查看 {len(medium_relevance)} 个中相关度文件。"
            f"低相关度文件（{len(low_relevance)} 个）可能只是偶然提及关键词，可跳过。"
        ),
    }


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='代码扫描辅助脚本 - 根据关键词定位与目标功能相关的源代码文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 扫描支付相关代码
  python %(prog)s ./my-project -k 支付,payment,pay,checkout -o payment-candidates.json

  # 扫描优惠券相关代码，显示详细输出
  python %(prog)s ./my-project -k coupon,优惠券,折扣 --verbose -o coupon-candidates.json

  # 只输出摘要到控制台
  python %(prog)s ./my-project -k auth,login,登录 --stdout
        """,
    )
    parser.add_argument('directory', help='要扫描的代码库根目录')
    parser.add_argument('-k', '--keywords', required=True,
                        help='关键词列表，逗号分隔（如：支付,payment,pay）')
    parser.add_argument('-o', '--output', default='candidates.json',
                        help='输出 JSON 文件路径（默认：candidates.json）')
    parser.add_argument('--verbose', action='store_true',
                        help='显示详细扫描进度')
    parser.add_argument('--stdout', action='store_true',
                        help='只输出摘要到控制台，不写文件')
    parser.add_argument('--top', type=int, default=0,
                        help='只输出前 N 个候选文件（0 表示全部）')

    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.exists() or not root.is_dir():
        print(f"错误：目录不存在或不是目录：{root}", file=sys.stderr)
        sys.exit(1)

    keywords = [kw.strip() for kw in args.keywords.split(',') if kw.strip()]
    if not keywords:
        print("错误：未提供有效关键词", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"开始扫描：{root}", file=sys.stderr)
        print(f"关键词：{keywords}", file=sys.stderr)

    candidates = scan_codebase(root, keywords, verbose=args.verbose)

    if args.top > 0:
        candidates = candidates[:args.top]

    summary = generate_summary(candidates, keywords)

    result = {
        'scan_root': str(root),
        'keywords': keywords,
        'summary': summary,
        'candidates': candidates,
    }

    if args.stdout:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        output_path = Path(args.output)
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"扫描完成，结果已保存到：{output_path}", file=sys.stderr)
        print(f"共找到 {len(candidates)} 个候选文件", file=sys.stderr)
        print(f"\n摘要：", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)


if __name__ == '__main__':
    main()
