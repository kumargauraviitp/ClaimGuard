"use client";

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, RefreshCw, AlertTriangle, TrendingUp } from 'lucide-react';
import { intelligenceApi } from '@/lib/intelligenceClient';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export default function IntelligenceDashboard() {
  const [loading, setLoading] = useState(true);
  const [driftData, setDriftData] = useState<any>(null);
  const [trendData, setTrendData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [drift, trends] = await Promise.all([
        intelligenceApi.checkConceptDrift(30),
        intelligenceApi.getFraudTrends(30)
      ]);
      setDriftData(drift);
      setTrendData(trends);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load intelligence data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Fraud Intelligence & Drift</h1>
        <Button onClick={fetchData} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Concept Drift Monitor */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="mr-2 h-5 w-5 text-yellow-500" /> 
              Model Concept Drift (Last 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {driftData?.status === 'insufficient_data' ? (
              <p className="text-sm text-gray-500">Not enough investigator feedback data to calculate drift.</p>
            ) : (
              <div className="space-y-4">
                <div className={`p-4 rounded-lg border ${driftData?.drift_detected ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                  <h3 className={`font-medium ${driftData?.drift_detected ? 'text-red-800' : 'text-green-800'}`}>
                    Status: {driftData?.drift_detected ? 'Drift Detected' : 'Stable'}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {driftData?.drift_detected 
                      ? 'The model exhibits higher than expected error rates. Consider reviewing the latest claims.' 
                      : 'The model continues to perform within acceptable bounds based on investigator feedback.'}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded-md border">
                    <p className="text-xs text-gray-500 uppercase font-semibold">Precision</p>
                    <p className="text-2xl font-bold">{(driftData?.metrics?.precision * 100)?.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md border">
                    <p className="text-xs text-gray-500 uppercase font-semibold">False Positive Rate</p>
                    <p className="text-2xl font-bold">{(driftData?.metrics?.fp_rate * 100)?.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md border">
                    <p className="text-xs text-gray-500 uppercase font-semibold">False Negative Rate</p>
                    <p className="text-2xl font-bold">{(driftData?.metrics?.fn_rate * 100)?.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md border">
                    <p className="text-xs text-gray-500 uppercase font-semibold">Total Evaluations</p>
                    <p className="text-2xl font-bold">{driftData?.metrics?.total_evaluations}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Trend Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="mr-2 h-5 w-5 text-blue-500" />
              Fraud Trends (Last 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {trendData?.trends?.length === 0 ? (
              <p className="text-sm text-gray-500">No trend data available for this period.</p>
            ) : (
              <div className="space-y-4">
                <div className="h-[250px] flex items-end gap-2 pt-4">
                  {trendData?.trends?.slice(-14).map((trend: any, idx: number) => {
                    const height = Math.max(10, trend.fraud_rate * 200);
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-2 group relative">
                        <div 
                          className="w-full bg-blue-500 rounded-t-sm transition-all group-hover:bg-blue-600"
                          style={{ height: `${height}px` }}
                        />
                        <span className="text-[10px] text-gray-500 transform -rotate-45 origin-top-left translate-y-2 translate-x-2">
                          {trend.date.split('-').slice(1).join('/')}
                        </span>
                        
                        {/* Tooltip */}
                        <div className="opacity-0 group-hover:opacity-100 absolute bottom-full mb-2 bg-gray-800 text-white text-xs p-2 rounded pointer-events-none whitespace-nowrap z-10 transition-opacity">
                          {trend.date}<br/>
                          Fraud Rate: {(trend.fraud_rate * 100).toFixed(1)}%<br/>
                          Cases: {trend.confirmed_fraud_cases} / {trend.total_cases_reviewed}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
