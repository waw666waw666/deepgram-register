"""
Base Site Adapter Definition.
Defines lifecycle and standard methods for automating web registration.
"""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from playwright.sync_api import Page, BrowserContext


class BaseSiteAdapter(ABC):
    """Abstract base class for all target site automation adapters."""

    def __init__(self, page: Page, context: BrowserContext, config: Optional[Dict[str, Any]] = None):
        self.page = page
        self.context = context
        self.config = config or {}
        self.account_data: Dict[str, Any] = {}

    @abstractmethod
    def target_url(self) -> str:
        """Return the registration or entry URL for this target site."""
        pass

    def prepare_identity(self) -> Dict[str, Any]:
        """Generate or retrieve synthetic credentials for this run."""
        return self.account_data

    @abstractmethod
    def fill_form(self, identity: Dict[str, Any]) -> bool:
        """Locate inputs and fill credentials into the form."""
        pass

    @abstractmethod
    def submit_and_confirm(self) -> bool:
        """Trigger form submission and handle simple post-submit verification."""
        pass

    def safe_navigate(self, url: str, timeout: int = 30000):
        """
        Navigate to URL safely, absorbing immediate client-side redirects or WAF reloads
        without crashing on 'Execution context was destroyed'.
        """
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        except Exception as e:
            err_str = str(e).lower()
            if "context was destroyed" in err_str or "navigation" in err_str:
                time.sleep(1)
                try:
                    self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
                except Exception:
                    pass
            else:
                raise

        # Settle buffer for client-side routing
        time.sleep(1.0)

    def run(self) -> bool:
        """Execute standard automation lifecycle sequentially."""
        url = self.target_url()
        self.safe_navigate(url)
        
        identity = self.prepare_identity()
        if not self.fill_form(identity):
            return False
            
        return self.submit_and_confirm()
