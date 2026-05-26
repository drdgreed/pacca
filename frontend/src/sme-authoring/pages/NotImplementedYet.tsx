/**
 * Placeholder for routes whose full pages land in PR-WUI-3 / PR-WUI-4.
 *
 * Renders an editorial "coming soon" page so the nav links work and the
 * routing topology is verified before the page content is filled in.
 */

import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';

interface NotImplementedYetProps {
  pageTitle: string;
  arrivingIn: string;
  body?: string;
}

export function NotImplementedYet({
  pageTitle,
  arrivingIn,
  body,
}: NotImplementedYetProps) {
  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader label="Surface" title={pageTitle} hint={`Arriving in ${arrivingIn}`} />
      <div className="sme-page-text">
        <p>
          {body ??
            'This page is under construction. The route is wired so the navigation works end-to-end; the page contents land in a subsequent PR per the approved Web UI plan.'}
        </p>
        <p>
          <Link to="/sme-author" className="sme-button sme-button-secondary">
            Back to dashboard
          </Link>
        </p>
      </div>
    </div>
  );
}
