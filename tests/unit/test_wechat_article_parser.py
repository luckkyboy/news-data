from __future__ import annotations

from pathlib import Path

import pytest

from app.infrastructure.parser.wechat_article_parser import WeChatArticleParser


def test_parse_wechat_article_fixture_extracts_metadata_and_news() -> None:
    html = Path("tests/fixtures/wechat_article_sample.html").read_text(encoding="utf-8")

    article = WeChatArticleParser().parse(html)

    assert article.title
    assert article.publish_date == "2026-03-27 06:30:00"
    assert article.cover == "https://example.com/cover.png"
    assert article.quote == "先照顾好自己，再去照顾世界"
    assert article.sources == ["人民日报", "新华社"]
    assert article.news == [
        "今天是个适合行动的日子",
        "把重要的事先做完",
    ]


def test_parse_wechat_article_raises_when_news_is_missing() -> None:
    html = """
    <html>
      <head>
        <title>示例</title>
      </head>
      <body>
        <h1 id="activity-name">示例标题</h1>
        <em id="publish_time">2026-03-27 06:30:00</em>
        <div id="page-content">
          <p>每日一句：先照顾好自己，再去照顾世界</p>
          <p>这不是编号内容</p>
        </div>
      </body>
    </html>
    """

    with pytest.raises(ValueError, match="news"):
        WeChatArticleParser().parse(html)


def test_parse_wechat_article_supports_jsdecode_create_time_and_bracketed_quote() -> None:
    html = """
    <html>
      <head>
        <title>示例</title>
      </head>
      <body>
        <h1 id="activity-name">3月27日，星期五，世界速览！</h1>
        <script>
          var msg = {
            create_time: JsDecode('2026-03-27 07:06')
          };
        </script>
        <div id="page-content">
          <p>1、第一条新闻</p>
          <p>2、第二条新闻</p>
          <p>【每日金句】每一次跌倒后的微笑，都是对生活最温柔，也最有力的回应。</p>
        </div>
      </body>
    </html>
    """

    article = WeChatArticleParser().parse(html)

    assert article.publish_date == "2026-03-27 07:06:00"
    assert article.quote == "每一次跌倒后的微笑，都是对生活最温柔，也最有力的回应"
    assert article.sources == []
    assert article.news == ["第一条新闻", "第二条新闻"]


def test_parse_wechat_article_filters_blacklisted_news_and_extracts_source() -> None:
    html = """
    <html>
      <body>
        <h1 id="activity-name">3月27日，星期五，每日简报</h1>
        <em id="publish_time">2026-03-27 07:06:00</em>
        <div id="page-content">
          <p>来源：央视新闻</p>
          <p>1、设置为星标，第一时间收到推送</p>
          <p>2、点击文末右下角，分享给朋友</p>
          <p>3、第一条新闻</p>
          <p>4、第二条新闻</p>
          <p>公众号ID：ghnews</p>
        </div>
      </body>
    </html>
    """

    article = WeChatArticleParser().parse(html)

    assert article.sources == ["央视新闻"]
    assert article.news == ["第一条新闻", "第二条新闻"]


def test_parse_wechat_article_greenjian_profile_extracts_source_from_section() -> None:
    html = """
    <html>
      <body>
        <h1 id="activity-name">3月27日，星期五，每日简报</h1>
        <em id="publish_time">2026-03-27 07:06:00</em>
        <div id="page-content">
          <p>1、第一条新闻</p>
          <p>2、第二条新闻</p>
          <section>
            <span>【新闻来源】: 澎湃新闻、人民日报、腾讯新闻、网易新闻、中国新闻网等</span>
          </section>
          <section>
            <span>绿健君微信二维码 欢迎添加 交个朋友</span>
          </section>
        </div>
      </body>
    </html>
    """

    article = WeChatArticleParser().parse(html, "greenjian")

    assert article.sources == ["澎湃新闻", "人民日报", "腾讯新闻", "网易新闻", "中国新闻网"]
    assert article.news == ["第一条新闻", "第二条新闻"]
