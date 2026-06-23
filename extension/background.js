chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'scanPhishGuard',
    title: 'Scan URL with PhishGuard',
    contexts: ['link', 'selection']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const url = info.linkUrl || info.selectionText || '';
  if (url) {
    chrome.storage.local.set({ pendingScan: url }, () => {
      chrome.action.openPopup();
    });
  }
});
