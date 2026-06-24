import apiClient from './apiClient';

export const intelligenceApi = {
    checkConceptDrift: async (windowDays: number = 30) => {
        const response = await apiClient.get(`/api/intelligence/drift/concept?window_days=${windowDays}`);
        return response.data;
    },
    
    analyzeFraudNetwork: async (claimId: string) => {
        const response = await apiClient.get(`/api/intelligence/analytics/network/${claimId}`);
        return response.data;
    },
    
    getFraudTrends: async (days: number = 30) => {
        const response = await apiClient.get(`/api/intelligence/analytics/trends?days=${days}`);
        return response.data;
    },
    
    getDecisionSupport: async (predictionId: string) => {
        const response = await apiClient.get(`/api/intelligence/recommendations/${predictionId}`);
        return response.data;
    },
    
    submitFeedback: async (data: {
        claim_id: string;
        prediction_id: string;
        final_decision: string;
        investigation_notes?: string;
        investigation_duration_hours?: number;
        fraud_confirmed: boolean;
        claim_approved: boolean;
    }) => {
        const response = await apiClient.post(`/api/feedback/submit`, data);
        return response.data;
    },
    
    getFeedbackHistory: async (skip: number = 0, limit: number = 100) => {
        const response = await apiClient.get(`/api/feedback/history?skip=${skip}&limit=${limit}`);
        return response.data;
    }
};
