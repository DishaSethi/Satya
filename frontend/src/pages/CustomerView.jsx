import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldCheck, ShoppingCart, Camera, Link as LinkIcon, Loader2, X, Terminal, ChevronDown } from 'lucide-react';
import api from '../services/api';

export default function CustomerView() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal & Sandbox State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Form State
  const [reviewText, setReviewText] = useState('');
//   const [unboxingImageUrl, setUnboxingImageUrl] = useState('');
  const [unboxingFile, setUnboxingFile] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState('empty');

  // Execution Terminal State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState([]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/customer/products');
      setProducts(response.data);
    } catch (err) {
      console.error("Fetch error:", err);
      setError(err.message || "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  // The Judge's Cheat Sheet (Demo Scenarios)
  const scenarios = {
    empty: { text: '', img: '' },
    happy: {
      text: 'Absolutely love it! Quality is top notch and it looks exactly like the picture. 10/10.',
      img: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?q=80&w=800' // Perfect Match
    },
    bait_switch: {
      text: 'Total scam! I ordered a premium jacket and received a literal trash bag. Give me a refund immediately!',
      img: 'https://images.unsplash.com/photo-1610557892470-55d9e80c0bce?q=80&w=800' // Trash Bag
    },
    sabotage: {
      text: 'TERRIBLE FAKE PRODUCT! ABSOLUTE SCAM GARBAGE! SELLER IS A FRAUD DO NOT BUY!!!',
      img: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?q=80&w=800' // Perfect Match (Contradiction!)
    }
  };

  const handleScenarioChange = (e) => {
    const key = e.target.value;
    setSelectedScenario(key);
    setReviewText(scenarios[key].text);
    // setUnboxingImageUrl(scenarios[key].img);
  };

  const openReviewModal = (product) => {
    setSelectedProduct(product);
    setReviewText('');
    setUnboxingFile(null);
    setSelectedScenario('empty');
    setTerminalLogs([]);
    setIsModalOpen(true);
  };

  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  // The Glass-Box Terminal Execution
  const runTerminalSimulation = async () => {
    const steps = [
      "> [API Gateway] Payload received. Pushing to Async Queue...",
      "> [Swarm Worker] Waking up LangGraph multi-agent network...",
      "> [Vision Agent] Extracting vector from Unboxing Image...",
      "> [Vision Agent] Comparing against Catalog Baseline Vector...",
      "> [NLP Agent] Analyzing review text sentiment & intent...",
      "> [Swarm Manager] Correlating Multimodal Data outputs...",
      "> [Ledger] Emitting verdicts to PostgreSQL Database...",
      "> [System] Agentic Swarm execution complete."
    ];

    setTerminalLogs([]);
    for (let step of steps) {
      setTerminalLogs(prev => [...prev, step]);
      await sleep(400); // Wait 400ms between logs for visual effect
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!reviewText || !unboxingFile) return alert("Please fill in all fields.");

    setIsSubmitting(true);

    try {
      // 1. Prepare real data for your FastAPI backend
      const formData = new FormData();
      formData.append('product_id', selectedProduct.id);
      formData.append('seller_id', selectedProduct.seller);
      formData.append('review_text', reviewText);
      formData.append('unboxing_image', unboxingFile);

      // 2. Fire the real API call and the Terminal Animation simultaneously
      await Promise.all([
        api.post('/api/customer/submit-review', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
        runTerminalSimulation()
      ]);

      // 3. Give the judge 1 second to read the final "execution complete" log
      await sleep(1000);

      setIsModalOpen(false);
      setIsSubmitting(false);

      // 4. Reload products to instantly show any UI Warning Patches!
      fetchProducts();

    } catch (err) {
      console.error("Submission error:", err);
      alert("Failed to submit review. Check backend.");
      setIsSubmitting(false);
    }
  };

  if (loading && products.length === 0) {
    return (
      <div className="flex justify-center items-center h-64 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-3 font-medium">Loading Marketplace Data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-700">
        <h2 className="text-lg font-bold flex items-center mb-2"><AlertTriangle className="w-5 h-5 mr-2" /> Frontend Error Detected</h2>
        <p className="font-mono text-sm bg-white p-3 rounded border border-red-100">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Marketplace</h1>
        <p className="text-slate-500 mt-1">Customer-facing product listings showing real-time Swarm governance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {products.map((product) => (
          <div key={product.id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm flex flex-col">
            <div className="h-64 overflow-hidden relative bg-slate-100">
              <img src={product.imageUrl} alt={product.title} className="w-full h-full object-cover" />
            </div>

            <div className="p-6 flex flex-col flex-grow">

              {product.uiWarningPatch && (
                <div className="mb-4 bg-orange-50 border border-orange-200 rounded-lg p-3 flex items-start space-x-3 text-orange-800 text-sm">
                  <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                  <span className="font-medium">{product.uiWarningPatch}</span>
                </div>
              )}

              {product.isClusteredMatch && (
                <div className="mb-4 inline-flex items-center space-x-1.5 bg-blue-50 text-blue-700 px-2.5 py-1 rounded-md text-xs font-medium border border-blue-100">
                  <LinkIcon className="w-3.5 h-3.5" />
                  <span>Clustered Match: Price Comparison Enabled</span>
                </div>
              )}

              <div className="flex justify-between items-start mb-2">
                <h2 className="text-xl font-bold text-slate-900">{product.title}</h2>
                <span className="text-lg font-bold text-indigo-600">{product.price}</span>
              </div>

              <div className="flex items-center space-x-1.5 text-slate-500 text-sm mb-6">
                <span>Sold by:</span>
                <span className="font-medium text-slate-700">{product.seller}</span>
                {!product.uiWarningPatch && <ShieldCheck className="w-4 h-4 text-emerald-500" />}
              </div>

              <div className="mt-auto space-y-3">
                <button className="w-full bg-slate-900 text-white font-medium py-2.5 rounded-lg hover:bg-slate-800 transition-colors flex items-center justify-center space-x-2">
                  <ShoppingCart className="w-4 h-4" />
                  <span>Add to Cart</span>
                </button>

                <button
                  onClick={() => openReviewModal(product)}
                  className="w-full bg-white border border-slate-300 text-slate-700 font-medium py-2 rounded-lg hover:bg-slate-50 transition-colors flex items-center justify-center space-x-2 text-sm"
                >
                  <Camera className="w-4 h-4" />
                  <span>Submit Unboxing Review</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* THE GLASS-BOX REVIEW MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">

            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <div>
                <h3 className="font-bold text-lg text-slate-900">Review: {selectedProduct?.title}</h3>
                <p className="text-xs text-slate-500">Test the Agentic Swarm logic in real-time</p>
              </div>
              {!isSubmitting && (
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            <div className="p-6 overflow-y-auto">
              {!isSubmitting ? (
                <form onSubmit={handleSubmitReview} className="space-y-5">

                  {/* Demo Cheat Sheet Dropdown */}
                  <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4">
                    <label className="block text-xs font-bold text-indigo-900 uppercase tracking-wider mb-2 flex items-center">
                      <ChevronDown className="w-4 h-4 mr-1" />
                      Test Data Library
                    </label>
                    <select
                      value={selectedScenario}
                      onChange={handleScenarioChange}
                      className="w-full bg-white border border-indigo-200 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    >
                      <option value="empty">-- Select a Demo Scenario or Type Manually --</option>
                      <option value="happy">Scenario A: Happy Customer (Perfect Match)</option>
                      <option value="bait_switch">Scenario B: Bait & Switch (Trash Bag)</option>
                      <option value="sabotage">Scenario C: Competitor Sabotage (Angry Text + Good Image)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Unboxing Review Text</label>
                    <textarea
                      required
                      rows={3}
                      value={reviewText}
                      onChange={(e) => setReviewText(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
                      placeholder="Write your review here..."
                    />
                  </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Unboxing Photo (Required)
                    </label>
                    <input
                      required
                      type="file"
                      accept="image/png, image/jpeg, image/jpg"
                      onChange={(e) => setUnboxingFile(e.target.files[0])}
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
                    />
                  </div>

                  <button type="submit" className="w-full bg-slate-900 text-white font-medium py-3 rounded-lg hover:bg-slate-800 transition-colors">
                    Push to Agentic Swarm
                  </button>
                </form>
              ) : (

                /* THE LIVE SWARM TERMINAL OVERLAY */
                <div className="bg-slate-950 rounded-xl p-5 border border-slate-800 shadow-inner h-64 overflow-hidden flex flex-col">
                  <div className="flex items-center space-x-2 border-b border-slate-800 pb-3 mb-3">
                    <Terminal className="w-5 h-5 text-emerald-400" />
                    <span className="text-emerald-400 font-mono text-sm font-semibold">LangGraph Execution Trace</span>
                    <Loader2 className="w-4 h-4 text-emerald-600 animate-spin ml-auto" />
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-2 font-mono text-xs text-emerald-500/80">
                    {terminalLogs.map((log, index) => (
                      <div key={index} className="animate-pulse">{log}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}