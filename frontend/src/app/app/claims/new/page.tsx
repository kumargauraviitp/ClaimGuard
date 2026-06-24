"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader, PageTransition } from "@/components/layout/page";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, Check, Car, User, FileText, Upload, ShieldCheck, AlertTriangle, Scale, Contact, Landmark, History, Save } from "lucide-react";

const steps = [
  { id: "customer", label: "Customer", icon: User },
  { id: "policy", label: "Policy", icon: ShieldCheck },
  { id: "vehicle", label: "Vehicle", icon: Car },
  { id: "accident", label: "Accident", icon: AlertTriangle },
  { id: "claim", label: "Financials", icon: Landmark },
  { id: "police", label: "Police", icon: Scale },
  { id: "witness", label: "Witness", icon: Contact },
  { id: "history", label: "History", icon: History },
  { id: "documents", label: "Uploads", icon: Upload },
] as const;

export default function NewClaimPage() {
  const router = useRouter();
  const [step, setStep] = React.useState(0);
  const [submitted, setSubmitted] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [files, setFiles] = React.useState<File[]>([]);
  
  const [form, setForm] = React.useState({
    status: "submitted",
    // Customer
    name: "", email: "", phone: "", city: "", age: "", gender: "", occupation: "",
    // Policy
    policyType: "", policyNumber: "", insuredValue: "",
    // Vehicle
    make: "", model: "", year: "", regNumber: "", color: "", vehicle_type: "", fuel_type: "", purchase_price: "", current_market_value: "",
    // Accident
    type: "", incidentDate: "", location: "", weather_conditions: "", road_conditions: "", description: "", vehicle_speed: "", number_of_vehicles_involved: "", number_of_injured: "",
    // Claim
    claimAmount: "", repair_estimate: "", medical_expenses: "", hospital_charges: "", towing_charges: "", additional_expenses: "",
    // Police
    hasPoliceReport: "no", police_report_number: "", police_station: "",
    // Witness
    witnesses: "no", witness_name: "", witness_contact: "", witness_details: "",
  });

  const update = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  
  const canNext = () => {
    // Basic validation
    if (step === 0) {
      if (!form.name || !form.email) return false;
      if (form.age && parseInt(form.age) < 18) return false; // Strict: Age > 18
      return true;
    }
    if (step === 1) return form.policyNumber && form.policyType;
    if (step === 2) return form.make && form.model;
    if (step === 3) {
      if (!form.incidentDate || !form.type) return false;
      const incidentDate = new Date(form.incidentDate);
      if (incidentDate > new Date()) return false; // Strict: No future dates
      return true;
    }
    if (step === 4) {
      if (!form.claimAmount || parseFloat(form.claimAmount) < 0) return false; // Strict: No negative financials
      return true;
    }
    if (step === 5) {
      if (form.hasPoliceReport === "yes" && !form.police_report_number) return false; // Strict: Mandatory if yes
    }
    return true;
  };

  const handleSubmit = async (isDraft = false) => {
    setIsSubmitting(true);
    try {
      const payload = {
        ...form,
        status: isDraft ? "draft" : "submitted",
        age: form.age ? parseInt(form.age) : null,
        year: form.year ? parseInt(form.year) : 2020,
        insuredValue: form.insuredValue ? parseFloat(form.insuredValue) : 0,
        purchase_price: form.purchase_price ? parseFloat(form.purchase_price) : null,
        current_market_value: form.current_market_value ? parseFloat(form.current_market_value) : null,
        vehicle_speed: form.vehicle_speed ? parseInt(form.vehicle_speed) : null,
        number_of_vehicles_involved: form.number_of_vehicles_involved ? parseInt(form.number_of_vehicles_involved) : null,
        number_of_injured: form.number_of_injured ? parseInt(form.number_of_injured) : null,
        claimAmount: form.claimAmount ? parseFloat(form.claimAmount) : 0,
        repair_estimate: form.repair_estimate ? parseFloat(form.repair_estimate) : null,
        medical_expenses: form.medical_expenses ? parseFloat(form.medical_expenses) : null,
        hospital_charges: form.hospital_charges ? parseFloat(form.hospital_charges) : null,
        towing_charges: form.towing_charges ? parseFloat(form.towing_charges) : null,
        additional_expenses: form.additional_expenses ? parseFloat(form.additional_expenses) : null,
      };

      const res = await apiClient.post("/api/claims", payload);
      const claimId = res.data?.id;

      if (claimId && files.length > 0 && !isDraft) {
        for (const file of files) {
          const formData = new FormData();
          formData.append("file", file);
          try {
            await apiClient.post(`/api/claims/${claimId}/documents`, formData);
          } catch (uploadErr) {
            console.error("Failed to upload document", uploadErr);
          }
        }
      }

      setSubmitted(true);
      if (isDraft) {
        toast.success("Draft saved successfully");
        router.push("/app/claims");
      } else {
        toast.success("Claim submitted successfully", { description: "Your claim is being processed." });
      }
    } catch (error) {
      toast.error("Submission failed", { description: "Please check your connection and try again." });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <PageTransition>
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-risk-low/15">
            <Check className="h-8 w-8 text-risk-low" />
          </div>
          <h2 className="font-heading text-2xl font-medium">Claim submitted</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Your claim has been securely saved to the database. The feature engineering layer will extract necessary features for the ML model.
          </p>
          <div className="mt-6 flex gap-3">
            <Button variant="outline" onClick={() => router.push("/app/claims")}>View claims</Button>
            <Button onClick={() => { setSubmitted(false); setStep(0); }}>Submit another</Button>
          </div>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <PageHeader eyebrow="Workspace" title="Submit a new claim" description="Complete the wizard to register a new automobile claim" />

      {/* Stepper */}
      <div className="mb-8 flex items-center gap-2 overflow-x-auto pb-2">
        {steps.map((s, i) => (
          <React.Fragment key={s.id}>
            <button
              onClick={() => i <= step && setStep(i)}
              className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition-colors ${i === step ? "bg-brand/15 text-brand" : i < step ? "bg-muted text-foreground" : "text-muted-foreground"}`}
            >
              <s.icon className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{s.label}</span>
              <span className="nums sm:hidden">{i + 1}</span>
            </button>
            {i < steps.length - 1 && <div className={`h-px flex-1 min-w-[20px] ${i < step ? "bg-brand/40" : "bg-border"}`} />}
          </React.Fragment>
        ))}
      </div>

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle className="text-lg">{steps[step].label} Details</CardTitle>
        </CardHeader>
        <CardContent>
          {step === 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div><Label>Full Name*</Label><Input placeholder="John Doe" value={form.name} onChange={(e) => update("name", e.target.value)} /></div>
              <div><Label>Email*</Label><Input type="email" placeholder="john@example.com" value={form.email} onChange={(e) => update("email", e.target.value)} /></div>
              <div><Label>Phone</Label><Input placeholder="+91 98765 43210" value={form.phone} onChange={(e) => update("phone", e.target.value)} /></div>
              <div><Label>City / Address</Label><Input placeholder="City, State" value={form.city} onChange={(e) => update("city", e.target.value)} /></div>
              <div>
                <Label>Age</Label>
                <Input type="number" placeholder="35" value={form.age} onChange={(e) => update("age", e.target.value)} />
                {form.age && parseInt(form.age) < 18 && <p className="mt-1 text-xs text-red-500">Customer must be over 18</p>}
              </div>
              <div>
                <Label>Gender</Label>
                <Select value={form.gender} onValueChange={(v) => update("gender", v)}>
                  <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                  <SelectContent><SelectItem value="male">Male</SelectItem><SelectItem value="female">Female</SelectItem><SelectItem value="other">Other</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="sm:col-span-2"><Label>Occupation</Label><Input placeholder="Engineer, Doctor, etc." value={form.occupation} onChange={(e) => update("occupation", e.target.value)} /></div>
            </div>
          )}

          {step === 1 && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div><Label>Policy Number*</Label><Input placeholder="POL-XX-000000" value={form.policyNumber} onChange={(e) => update("policyNumber", e.target.value)} /></div>
              <div>
                <Label>Policy Type*</Label>
                <Select value={form.policyType} onValueChange={(v) => update("policyType", v)}>
                  <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="comprehensive">Comprehensive</SelectItem>
                    <SelectItem value="third_party">Third Party</SelectItem>
                    <SelectItem value="zero_depreciation">Zero Depreciation</SelectItem>
                    <SelectItem value="own_damage">Own Damage</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Coverage Amount (₹)*</Label><Input type="number" placeholder="1500000" value={form.insuredValue} onChange={(e) => update("insuredValue", e.target.value)} /></div>
            </div>
          )}

          {step === 2 && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div><Label>Registration Number*</Label><Input placeholder="MH-12-XX-0000" value={form.regNumber} onChange={(e) => update("regNumber", e.target.value)} /></div>
              <div><Label>Manufacturer*</Label><Input placeholder="e.g. Hyundai" value={form.make} onChange={(e) => update("make", e.target.value)} /></div>
              <div><Label>Model*</Label><Input placeholder="e.g. Creta" value={form.model} onChange={(e) => update("model", e.target.value)} /></div>
              <div><Label>Year*</Label><Input type="number" placeholder="2022" value={form.year} onChange={(e) => update("year", e.target.value)} /></div>
              <div><Label>Vehicle Type</Label><Input placeholder="SUV, Sedan, Hatchback" value={form.vehicle_type} onChange={(e) => update("vehicle_type", e.target.value)} /></div>
              <div>
                <Label>Fuel Type</Label>
                <Select value={form.fuel_type} onValueChange={(v) => update("fuel_type", v)}>
                  <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="petrol">Petrol</SelectItem>
                    <SelectItem value="diesel">Diesel</SelectItem>
                    <SelectItem value="ev">Electric</SelectItem>
                    <SelectItem value="cng">CNG</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Color</Label><Input placeholder="Color" value={form.color} onChange={(e) => update("color", e.target.value)} /></div>
              <div><Label>Current Market Value (₹)</Label><Input type="number" placeholder="1200000" value={form.current_market_value} onChange={(e) => update("current_market_value", e.target.value)} /></div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label>Accident Type*</Label>
                  <Select value={form.type} onValueChange={(v) => update("type", v)}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="own_damage">Own Damage</SelectItem>
                      <SelectItem value="third_party">Third Party</SelectItem>
                      <SelectItem value="theft">Theft</SelectItem>
                      <SelectItem value="natural_disaster">Natural Disaster</SelectItem>
                      <SelectItem value="personal_injury">Personal Injury</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Incident Date*</Label>
                  <Input type="date" value={form.incidentDate} onChange={(e) => update("incidentDate", e.target.value)} />
                  {form.incidentDate && new Date(form.incidentDate) > new Date() && <p className="mt-1 text-xs text-red-500">Accident date cannot be in the future</p>}
                </div>
                <div><Label>Location</Label><Input placeholder="City, Highway, Intersection" value={form.location} onChange={(e) => update("location", e.target.value)} /></div>
                <div><Label>Vehicle Speed (km/h)</Label><Input type="number" placeholder="60" value={form.vehicle_speed} onChange={(e) => update("vehicle_speed", e.target.value)} /></div>
                <div><Label>Weather Conditions</Label><Input placeholder="Rainy, Clear, Foggy" value={form.weather_conditions} onChange={(e) => update("weather_conditions", e.target.value)} /></div>
                <div><Label>Road Conditions</Label><Input placeholder="Wet, Dry, Potholes" value={form.road_conditions} onChange={(e) => update("road_conditions", e.target.value)} /></div>
                <div><Label>Vehicles Involved</Label><Input type="number" placeholder="2" value={form.number_of_vehicles_involved} onChange={(e) => update("number_of_vehicles_involved", e.target.value)} /></div>
                <div><Label>Injured Persons</Label><Input type="number" placeholder="0" value={form.number_of_injured} onChange={(e) => update("number_of_injured", e.target.value)} /></div>
              </div>
              <div><Label>Accident Description</Label><Textarea rows={3} placeholder="Describe exactly what happened…" value={form.description} onChange={(e) => update("description", e.target.value)} /></div>
            </div>
          )}

          {step === 4 && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Label>Total Claim Amount (₹)*</Label>
                <Input type="number" className="text-lg" placeholder="250000" value={form.claimAmount} onChange={(e) => update("claimAmount", e.target.value)} />
                {form.claimAmount && parseFloat(form.claimAmount) < 0 && <p className="mt-1 text-xs text-red-500">Amount cannot be negative</p>}
              </div>
              <div><Label>Repair Estimate (₹)</Label><Input type="number" placeholder="150000" value={form.repair_estimate} onChange={(e) => update("repair_estimate", e.target.value)} /></div>
              <div><Label>Medical Expenses (₹)</Label><Input type="number" placeholder="0" value={form.medical_expenses} onChange={(e) => update("medical_expenses", e.target.value)} /></div>
              <div><Label>Hospital Charges (₹)</Label><Input type="number" placeholder="0" value={form.hospital_charges} onChange={(e) => update("hospital_charges", e.target.value)} /></div>
              <div><Label>Towing Charges (₹)</Label><Input type="number" placeholder="2000" value={form.towing_charges} onChange={(e) => update("towing_charges", e.target.value)} /></div>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-4">
              <div>
                <Label>Police Report / FIR Filed?</Label>
                <Select value={form.hasPoliceReport} onValueChange={(v) => update("hasPoliceReport", v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="yes">Yes</SelectItem><SelectItem value="no">No</SelectItem></SelectContent>
                </Select>
              </div>
              {form.hasPoliceReport === "yes" && (
                <div className="grid gap-4 sm:grid-cols-2 animate-in fade-in slide-in-from-top-2">
                  <div>
                    <Label>FIR Number*</Label>
                    <Input placeholder="FIR-12345" value={form.police_report_number} onChange={(e) => update("police_report_number", e.target.value)} />
                    {!form.police_report_number && <p className="mt-1 text-xs text-red-500">Required if Police Report is filed</p>}
                  </div>
                  <div><Label>Police Station</Label><Input placeholder="Central Police Station" value={form.police_station} onChange={(e) => update("police_station", e.target.value)} /></div>
                </div>
              )}
            </div>
          )}

          {step === 6 && (
            <div className="space-y-4">
              <div>
                <Label>Were there any witnesses?</Label>
                <Select value={form.witnesses} onValueChange={(v) => update("witnesses", v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="yes">Yes</SelectItem><SelectItem value="no">No</SelectItem></SelectContent>
                </Select>
              </div>
              {form.witnesses === "yes" && (
                <div className="grid gap-4 sm:grid-cols-2 animate-in fade-in slide-in-from-top-2">
                  <div><Label>Witness Name</Label><Input placeholder="Jane Doe" value={form.witness_name} onChange={(e) => update("witness_name", e.target.value)} /></div>
                  <div><Label>Witness Contact</Label><Input placeholder="+91 98765 00000" value={form.witness_contact} onChange={(e) => update("witness_contact", e.target.value)} /></div>
                  <div className="sm:col-span-2"><Label>Witness Statement</Label><Textarea rows={2} placeholder="Brief summary of witness statement..." value={form.witness_details} onChange={(e) => update("witness_details", e.target.value)} /></div>
                </div>
              )}
            </div>
          )}

          {step === 7 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">This section fetches the customer's previous claims from the database to assist investigators.</p>
              <div className="rounded-xl border bg-muted/50 p-4">
                <div className="flex items-center gap-3">
                  <History className="h-5 w-5 text-muted-foreground" />
                  <span className="font-medium">Previous Claim History (Read Only)</span>
                </div>
                <div className="mt-4 grid gap-4 text-sm sm:grid-cols-3">
                  <div><p className="text-muted-foreground">Previous Claims</p><p className="font-medium nums">0</p></div>
                  <div><p className="text-muted-foreground">Fraud Cases</p><p className="font-medium nums">0</p></div>
                  <div><p className="text-muted-foreground">Claim Frequency</p><p className="font-medium">Low</p></div>
                </div>
              </div>
            </div>
          )}

          {step === 8 && (
            <div className="flex flex-col items-center py-10 text-center">
              <Upload className="mb-3 h-10 w-10 text-muted-foreground" />
              <p className="text-sm font-medium">Upload supporting documents</p>
              <p className="mt-1 text-xs text-muted-foreground">Vehicle images, Police FIR, Repair estimates, Medical bills</p>
              <div className="mt-4 flex flex-col items-center">
                <input 
                  type="file" 
                  id="file-upload" 
                  className="hidden" 
                  multiple 
                  onChange={(e) => {
                    if (e.target.files) {
                      setFiles(Array.from(e.target.files));
                    }
                  }} 
                />
                <Label htmlFor="file-upload" className="cursor-pointer">
                  <div className="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 gap-1.5">
                    Choose files
                  </div>
                </Label>
                {files.length > 0 && (
                  <div className="mt-4 text-sm w-full max-w-sm">
                    <p className="font-medium mb-2 text-center">Selected files:</p>
                    <ul className="space-y-1">
                      {files.map((file, i) => (
                        <li key={i} className="text-muted-foreground truncate text-center">{file.name}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {form.hasPoliceReport === "yes" && (
                <p className="mt-3 text-xs text-red-500 font-medium">Police Report upload is mandatory because you selected Yes in Police Details.</p>
              )}
            </div>
          )}

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Button variant="ghost" onClick={() => step > 0 ? setStep(step - 1) : router.push("/app/claims")} className="gap-1.5" disabled={step === 0 && isSubmitting}>
              <ArrowLeft className="h-4 w-4" /> {step === 0 ? "Cancel" : "Back"}
            </Button>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => handleSubmit(true)} disabled={isSubmitting || !form.email} className="gap-1.5">
                <Save className="h-4 w-4" /> Save Draft
              </Button>
              
              {step < steps.length - 1 ? (
                <Button onClick={() => setStep(step + 1)} disabled={!canNext()} className="gap-1.5 bg-secondary text-secondary-foreground hover:bg-secondary/80">
                  Next Step <ArrowRight className="h-4 w-4" />
                </Button>
              ) : (
                <Button onClick={() => handleSubmit(false)} disabled={isSubmitting || !canNext()} className="gap-1.5 bg-brand text-primary-foreground hover:bg-brand/90">
                  {isSubmitting ? "Submitting..." : "Submit Complete Claim"}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </PageTransition>
  );
}
