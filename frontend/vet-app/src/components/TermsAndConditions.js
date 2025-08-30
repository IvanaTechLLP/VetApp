import React from "react";

const TermsAndConditions = () => {
  return (
    <div className="max-w-3xl mx-auto p-6 text-gray-800">
      <h1 className="text-3xl font-bold mb-4">Purry Tails – Terms & Conditions</h1>
      
      <h2 className="text-xl font-semibold mt-4">1. Introduction</h2>
      <p className="mb-4">Welcome to Purry Tails! By accessing or using our services, you agree to comply with these Terms & Conditions (T&C). These terms govern your use of our platform, including subscriptions, AI-powered pet health records, and veterinary consultations. If you do not agree to these terms, please do not use our services.</p>
      
      <h2 className="text-xl font-semibold mt-4">2. Definitions</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>“Purry Tails” refers to our platform, website, and services.</li>
        <li>“User” refers to any individual who creates an account and uses our services.</li>
        <li>“Subscription” refers to the paid plans (Monthly, 6-Month, and 12-Month).</li>
        <li>“Services” include digital pet health records, AI-based medical summaries, and vet consultations.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">3. Eligibility</h2>
      <p className="mb-4">You must be 18 years or older to use our services. By registering, you confirm that you have the legal right to enter into this agreement.</p>
      
      <h2 className="text-xl font-semibold mt-4">4. Data Privacy & User Information</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>Personal information such as phone number, email, and location will remain private and confidential.</li>
        <li>Pet-related information (such as medical history, breed, and vaccination records) is required.</li>
        <li>Users agree to provide accurate and complete pet data for AI-generated health summaries and medical consultations.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">5. Subscriptions & Payments</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>We offer Monthly, 6-Month, and 12-Month subscription plans.</li>
        <li>Payments are processed securely via Razorpay.</li>
        <li>Subscriptions auto-renew unless canceled before the renewal date.</li>
        <li>If a payment fails, access to services may be temporarily suspended until the issue is resolved.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">6. Cancellation & Refunds</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>Users can cancel subscriptions at any time (see Cancellation Policy below).</li>
        <li>Refunds are issued only under certain conditions (see Refund Policy below).</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">7. Acceptable Use Policy</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>Users must not misuse or alter AI-generated pet health summaries.</li>
        <li>Veterinary consultations provided on the platform are for guidance purposes only.</li>
        <li>Users must not upload misleading or fraudulent information.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">8. Intellectual Property Rights</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>All AI-generated reports, UI/UX designs, and service content belong to Purry Tails.</li>
        <li>Users may not copy, distribute, or commercially exploit any content without written permission.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">9. Limitation of Liability</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>Purry Tails is not liable for any incorrect medical interpretations of AI-generated reports.</li>
        <li>We are not responsible for third-party service interruptions or data loss.</li>
        <li>Unauthorized access to personal accounts due to user negligence is not our responsibility.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">10. Termination of Services</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>We reserve the right to suspend or terminate accounts that violate these Terms & Conditions.</li>
        <li>Accounts involved in fraudulent activities or abuse of the platform may be terminated.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">11. Governing Law</h2>
      <p className="mb-4">These Terms & Conditions are governed by the laws of India. Any disputes will be resolved in courts located in [Your Business’s Jurisdiction].</p>
      
      <h2 className="text-xl font-semibold mt-4">Cancellation Policy</h2>
      <ul className="list-disc pl-6 mb-4">
        <li>Users can cancel their Monthly, 6-Month, or 12-Month subscription plans at any time via account settings.</li>
        <li>Once canceled, the subscription remains active until the end of the billing cycle, and no further charges will be applied.</li>
        <li>No mid-term cancellations: Users will continue to have access until the period expires.</li>
        <li>Once a subscription is canceled, it cannot be reactivated mid-term. Users must purchase a new subscription.</li>
      </ul>
      
      <h2 className="text-xl font-semibold mt-4">Refund Policy</h2>
      <h3 className="text-lg font-semibold mt-3">1. No Refunds for Used Subscription Periods</h3>
      <p className="mb-4">We do not offer refunds for any used portion of a subscription. Once a plan starts, it is considered non-refundable.</p>
      
      <h3 className="text-lg font-semibold mt-3">2. Refunds for Service Disruptions</h3>
      <p className="mb-4">If Purry Tails is unable to provide services for an extended period due to technical issues, a pro-rata refund may be issued based on the remaining days of the subscription. Refunds will be processed through Razorpay within 7-10 business days.</p>
      
      <h3 className="text-lg font-semibold mt-3">3. Duplicate Transactions & Billing Errors</h3>
      <p className="mb-4">If a user is wrongly charged twice, the excess amount will be refunded automatically. In case of billing disputes, users should contact info@purrytails.in within 7 days of the transaction.</p>
    </div>
  );
};

export default TermsAndConditions;
