"""Offline Chromium smoke test of v24.3 scheduler + passive read-only bridge."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from test_passive_bridge import HTML, NEW_ACTIVE
BASE=Path(__file__).parent
async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=await browser.new_page()
        await page.goto('about:blank')
        await page.set_content(HTML)
        await page.evaluate('''() => {window.__routes=[];window.chrome={runtime:{lastError:null,sendMessage:(msg,cb)=>{window.__routes.push(msg);cb({ok:true})}}};}''')
        before=await page.locator('body').inner_html()
        # about:blank is an opaque origin; patch only the offline test copies.
        refresh=(BASE/'refresh_2s.js').read_text().replace("const onDeals=()=>/^\\/flips\\/deals\\/?$/.test(location.pathname);","const onDeals=()=>true;")
        refresh=refresh.replace("const onDeals=()=>/^\/flips\/deals\/?$/.test(location.pathname);","const onDeals=()=>true;")
        refresh=refresh.replace("},location.origin);","},'*');")
        bridge=(BASE/'content.js').read_text()
        bridge='\n'.join('  const isDealsPage = () => true;' if line.strip().startswith('const isDealsPage =') else line for line in bridge.splitlines())
        bridge=bridge.replace("},location.origin);","},'*');")
        await page.evaluate(refresh)
        await page.evaluate(bridge)
        await page.wait_for_timeout(2300)
        status=await page.evaluate('window.__fmRushSoftRefreshV243.status()')
        assert status['attempts']>=1,status
        assert status['dealsOnPage']==0,status
        assert status['resourceRequests']==0,status
        assert status['lastNetworkAt'] is None,status
        assert before==await page.locator('body').inner_html(),'Original page DOM was modified'
        await page.evaluate('(html)=>document.querySelector("#list").insertAdjacentHTML("beforeend",html)',NEW_ACTIVE)
        await page.wait_for_timeout(350)
        status=await page.evaluate('window.__fmRushSoftRefreshV243.status()')
        assert status['dealsOnPage']==1,status
        assert status['dataChanges']>=1,status
        assert len(await page.evaluate('window.__routes'))==1
        await browser.close()
        print('PASS v24.3 Chromium: simulated page, no DOM changes, signals, baseline, DOM changes, fresh deal forwarding')
if __name__=='__main__': asyncio.run(main())
