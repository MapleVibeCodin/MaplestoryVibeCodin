"""Offline Chromium integration check for passive, read-only deal forwarding.
Run: python browser_extension/test_passive_bridge.py
Requires playwright and a locally installed Chromium (or Playwright Chromium).
No calls are made to HeneFM or any other website.
"""
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

BASE=Path(__file__).parent
HTML='''<!DOCTYPE html><html><body>
<style>body{margin:24px}article{padding:8px;border:1px solid #bbb}</style>
<header><h1 id="original">HeneFM — original Flips</h1><button id="apply">Apply</button></header>
<main id="list">
<article id="existing"><a href="https://henefm.com/items/100">Blue Starlight</a>
<div>Equipment · Overall</div><span>W.DEF 57 · INT 9</span>
<div>Profit</div><strong>+22.3K</strong><span>34%</span>
<div>Buy</div><b>65K</b><a href="https://henefm.com/shops/Hyperborean">Hyperborean</a>
<div>CH 30 · FM 5</div><div>Seen 4m ago</div><div>84 sold a day</div></article>
<article id="existing-sold"><a href="https://henefm.com/items/101">Heckler</a><span>Sold</span>
<div>Profit +100K 50%</div><div>Buy 100K</div><a href="https://henefm.com/shops/Arkne">Arkne</a>
<div>CH 2 · FM 15</div><div>Sold 9m ago</div></article>
</main></body></html>'''
NEW_ACTIVE='''<article id="new-active"><a href="https://henefm.com/items/102">Work Gloves</a><div>CRIT 2</div>
<div>Profit +233.2K 130%</div><div>Buy 180K</div>
<a href="https://henefm.com/shops/FantonRR">FantonRR</a><div>CH 10 · FM 14</div>
<div>Seen 20s ago</div><div>103 sold a day</div></article>'''
NEW_SOLD='''<article id="new-sold"><a href="https://henefm.com/items/103">Wand Scroll</a><span>Sold</span>
<div>Profit +217.1K 109%</div><div>Buy 200K</div>
<a href="https://henefm.com/shops/HazelGeek">HazelGeek</a><div>CH 3 · FM 18</div></article>'''
NEW_MULTI='''<article id="new-multi"><a href="https://henefm.com/items/104">Armor Scroll: Greater</a>
<div>Profit · all 3 +47.7K +15.9K each 1026%</div>
<div>Buy 1.6K</div><div>3 items · 4.7K total</div>
<a href="https://henefm.com/shops/UrMyVuln">UrMyVuln</a><div>CH 3 · FM 16</div><div>Seen 9m ago</div></article>'''

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=await browser.new_page()
        await page.goto('about:blank')
        await page.set_content(HTML)
        await page.evaluate('''() => {
            window.__routes=[];window.__live=[];
            window.chrome={runtime:{lastError:null,sendMessage:(msg,cb)=>{
                if(msg.kind==='fm-rush-route-deal')window.__routes.push(msg);
                if(msg.kind==='fm-rush-visible-deals')window.__live.push(msg.snapshot);cb({ok:true});
            }}};
        }''')
        before=await page.locator('body').inner_html()
        # Only override location gate for this offline test; production source is untouched.
        source=(BASE/'content.js').read_text()
        source='\n'.join('  const isDealsPage = () => true;' if line.strip().startswith('const isDealsPage =') else line for line in source.splitlines())
        await page.evaluate(source)
        await page.wait_for_timeout(300)
        after=await page.locator('body').inner_html()
        assert before==after,'Extension changed HeneFM page DOM'
        assert await page.locator('#fm-rush-deals-only-view').count()==0
        assert await page.evaluate('window.__routes.length')==2,'All visible listings must route on startup, including displayed sold cards'
        await page.evaluate('(html) => document.querySelector("#list").insertAdjacentHTML("beforeend",html)',NEW_ACTIVE+NEW_SOLD+NEW_MULTI)
        await page.wait_for_timeout(550)
        routes=await page.evaluate('window.__routes.map(r=>r.deal)')
        assert len(routes)==5,f'Expected all five rendered listings, got {routes}'
        assert set(x['ign'] for x in routes)=={'Hyperborean','Arkne','FantonRR','HazelGeek','UrMyVuln'},routes
        assert all(x['profit_percent']>=15 and x['profit_mesos']>=15000 for x in routes)
        assert await page.locator('#original').inner_text()=='HeneFM — original Flips'
        assert await page.locator('#apply').is_visible()
        assert await page.locator('#fm-rush-deals-only-view').count()==0
        # Mutation on previously seen deal should never route a duplicate.
        await page.locator('#new-active').evaluate('(el)=>el.appendChild(document.createElement("small")).textContent="Updated"')
        await page.wait_for_timeout(220)
        assert await page.evaluate('window.__routes.length')==5,'Duplicate deal on DOM mutation'
        # Changing only the displayed age of a sold card must not duplicate it.
        await page.locator('#new-sold').evaluate('(el)=>el.querySelector("span").textContent="Sold 1h ago"')
        await page.wait_for_timeout(200)
        assert await page.evaluate('window.__routes.length')==5
        assert set(await page.evaluate('window.__live.at(-1).deals.map(d=>d.ign)'))=={'Hyperborean','Arkne','FantonRR','HazelGeek','UrMyVuln'}
        await page.locator('#list').evaluate('(el)=>el.innerHTML=""')
        await page.wait_for_timeout(250)
        assert await page.evaluate('window.__live.at(-1).deals.length')==0,'An empty page must clear active scan names'
        await browser.close()
        print('PASS: page DOM unchanged, all rendered active/sold listings delivered, multi-item profit, no duplicate sends; live snapshots follow page rotation')

if __name__=='__main__':asyncio.run(main())
