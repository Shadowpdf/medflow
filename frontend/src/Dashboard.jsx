import { useEffect, useState } from "react";
import api from "./api";
import "./Dashboard.css";

function Dashboard({ onLogout }) {
    const [hospitals, setHospitals] = useState([]);
    const [equipment, setEquipment] = useState([]);
    const [workOrders, setWorkOrders] = useState([]);
    const [serviceReports, setServiceReports] = useState([]);
    const [activePage, setActivePage] = useState("dashboard");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [user, setUser] = useState(null);
    const [reportWorkOrderId, setReportWorkOrderId] = useState("");
    const [reportFileUrl, setReportFileUrl] = useState("");
    const [reportNotes, setReportNotes] = useState("");
    const [hospitalName, setHospitalName] = useState("");
    const [hospitalRegion, setHospitalRegion] = useState("");
    const [hospitalCapacity, setHospitalCapacity] = useState("");
    const [hospitalSupervisor, setHospitalSupervisor] = useState("");
    const [equipmentSerial, setEquipmentSerial] = useState("");
    const [equipmentModel, setEquipmentModel] = useState("");
    const [equipmentStatus, setEquipmentStatus] = useState("Available");
    const [equipmentCharge, setEquipmentCharge] = useState("");
    const [equipmentFacility, setEquipmentFacility] = useState("");
    const [workOrderTitle, setWorkOrderTitle] = useState("");
    const [workOrderPriority, setWorkOrderPriority] = useState("Medium");
    const [workOrderStatus, setWorkOrderStatus] = useState("Pending");
    const [workOrderEquipment, setWorkOrderEquipment] = useState("");
    const [workOrderTechnician, setWorkOrderTechnician] = useState("");

    const isAdmin = user?.role === "Clinical Admin";
    const isTechnician = user?.role === "Field Technician";
    const isAuditor = user?.role === "Auditor";

    useEffect(() => {
        const loadData = async () => {
            try {
                const [
                    userResponse,
                    hospitalsResponse,
                    equipmentResponse,
                    workOrdersResponse,
                    serviceReportsResponse,
                ] = await Promise.all([
                    api.get("/auth/me"),
                    api.get("/hospitals/"),
                    api.get("/equipment/"),
                    api.get("/work-orders/"),
                    api.get("/service-reports/"),
                ]);

                setUser(userResponse.data);
                setHospitals(hospitalsResponse.data);
                setEquipment(equipmentResponse.data);
                setWorkOrders(workOrdersResponse.data);
                setServiceReports(serviceReportsResponse.data);
            } catch (error) {
                console.error(error);
                setError("Unable to load MedFlow data.");
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    if (loading) {
        return <h2>Loading MedFlow...</h2>;
    }

    const updateWorkOrderStatus = async (workOrderId, newStatus) => {
        try {
            const response = await api.patch(
                `/work-orders/${workOrderId}/status`,
                {
                    status: newStatus,
                }
            );

            setWorkOrders((currentOrders) =>
                currentOrders.map((order) =>
                    order.id === workOrderId
                        ? response.data
                        : order
                )
            );
        } catch (error) {
            console.error(error);
            setError("Unable to update work order.");
        }
    };

    const createServiceReport = async (event) => {
        event.preventDefault();
        setError("");

        try {
            const response = await api.post("/service-reports/", {
                work_order_id: Number(reportWorkOrderId),
                file_url: reportFileUrl,
                notes: reportNotes || null,
            });

            setServiceReports((currentReports) => [
                ...currentReports,
                response.data,
            ]);

            setReportWorkOrderId("");
            setReportFileUrl("");
            setReportNotes("");
        } catch (error) {
            console.error(error);
            setError("Unable to create service report.");
        }
    };

    const createHospital = async (event) => {
        event.preventDefault();
        setError("");

        try {
            const response = await api.post("/hospitals/", {
                name: hospitalName,
                location_region: hospitalRegion,
                capacity: Number(hospitalCapacity),
                supervisor_id: Number(hospitalSupervisor),
            });

            setHospitals((currentHospitals) => [
                ...currentHospitals,
                response.data,
            ]);

            setHospitalName("");
            setHospitalRegion("");
            setHospitalCapacity("");
            setHospitalSupervisor("");
        } catch (error) {
            console.error(error);
            setError("Unable to create hospital.");
        }
    };

    const createEquipment = async (event) => {
        event.preventDefault();
        setError("");

        try {
            const response = await api.post("/equipment/", {
                serial_number: equipmentSerial,
                model: equipmentModel,
                status: equipmentStatus,
                charge_level: Number(equipmentCharge),
                facility_id: Number(equipmentFacility),
            });

            setEquipment((currentEquipment) => [
                ...currentEquipment,
                response.data,
            ]);

            setEquipmentSerial("");
            setEquipmentModel("");
            setEquipmentStatus("Available");
            setEquipmentCharge("");
            setEquipmentFacility("");
        } catch (error) {
            console.error(error);
            setError("Unable to create equipment.");
        }
    };
    const createWorkOrder = async (event) => {
        event.preventDefault();
        setError("");

        try {
            const response = await api.post("/work-orders/", {
                title: workOrderTitle,
                priority: workOrderPriority,
                status: workOrderStatus,
                equipment_id: Number(workOrderEquipment),
                technician_id: Number(workOrderTechnician),
            });

            setWorkOrders((currentOrders) => [
                ...currentOrders,
                response.data,
            ]);

            setWorkOrderTitle("");
            setWorkOrderPriority("Medium");
            setWorkOrderStatus("Pending");
            setWorkOrderEquipment("");
            setWorkOrderTechnician("");
        } catch (error) {
            console.error(error);
            setError("Unable to create work order.");
        }
    };

    const renderDashboard = () => (
        <>
            <h1>Dashboard</h1>
            <p className="subtitle">MedFlow system overview</p>

            <div className="cards">
                <div className="card">
                    <h3>Hospitals</h3>
                    <span>{hospitals.length}</span>
                </div>

                <div className="card">
                    <h3>Equipment</h3>
                    <span>{equipment.length}</span>
                </div>

                <div className="card">
                    <h3>Work Orders</h3>
                    <span>{workOrders.length}</span>
                </div>

                <div className="card">
                    <h3>Service Reports</h3>
                    <span>{serviceReports.length}</span>
                </div>
            </div>
        </>
    );

    const renderHospitals = () => (
        <>
            <h1>Hospitals</h1>

            {isAdmin && (
                <form
                    className="action-form"
                    onSubmit={createHospital}
                >
                    <h3>Add Hospital</h3>

                    <label>Name</label>
                    <input
                        type="text"
                        value={hospitalName}
                        onChange={(event) =>
                            setHospitalName(event.target.value)
                        }
                        required
                    />

                    <label>Region</label>
                    <input
                        type="text"
                        value={hospitalRegion}
                        onChange={(event) =>
                            setHospitalRegion(event.target.value)
                        }
                        required
                    />

                    <label>Capacity</label>
                    <input
                        type="number"
                        min="1"
                        value={hospitalCapacity}
                        onChange={(event) =>
                            setHospitalCapacity(event.target.value)
                        }
                        required
                    />

                    <label>Supervisor ID</label>
                    <input
                        type="number"
                        value={hospitalSupervisor}
                        onChange={(event) =>
                            setHospitalSupervisor(event.target.value)
                        }
                        required
                    />

                    <button type="submit">
                        Add Hospital
                    </button>
                </form>
            )}

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Region</th>
                        <th>Capacity</th>
                        <th>Supervisor</th>
                    </tr>
                </thead>

                <tbody>
                    {hospitals.map((hospital) => (
                        <tr key={hospital.id}>
                            <td>{hospital.id}</td>
                            <td>{hospital.name}</td>
                            <td>{hospital.location_region}</td>
                            <td>{hospital.capacity}</td>
                            <td>{hospital.supervisor_id}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );

    const renderEquipment = () => (
        <>
            <h1>Equipment</h1>

            {isAdmin && (
                <form className="action-form" onSubmit={createEquipment}>
                    <h3>Add Equipment</h3>

                    <label>Serial Number</label>
                    <input
                        value={equipmentSerial}
                        onChange={(event) =>
                            setEquipmentSerial(event.target.value)
                        }
                        required
                    />

                    <label>Model</label>
                    <input
                        value={equipmentModel}
                        onChange={(event) =>
                            setEquipmentModel(event.target.value)
                        }
                        required
                    />

                    <label>Status</label>
                    <select
                        value={equipmentStatus}
                        onChange={(event) =>
                            setEquipmentStatus(event.target.value)
                        }
                    >
                        <option value="Available">Available</option>
                        <option value="In-Use">In-Use</option>
                        <option value="Maintenance">Maintenance</option>
                        <option value="Offline">Offline</option>
                    </select>

                    <label>Charge Level</label>
                    <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        value={equipmentCharge}
                        onChange={(event) =>
                            setEquipmentCharge(event.target.value)
                        }
                        required
                    />

                    <label>Hospital</label>
                    <select
                        value={equipmentFacility}
                        onChange={(event) =>
                            setEquipmentFacility(event.target.value)
                        }
                        required
                    >
                        <option value="">Select hospital</option>

                        {hospitals.map((hospital) => (
                            <option key={hospital.id} value={hospital.id}>
                                {hospital.name}
                            </option>
                        ))}
                    </select>

                    <button type="submit">Add Equipment</button>
                </form>
            )}

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Serial Number</th>
                        <th>Model</th>
                        <th>Status</th>
                        <th>Charge</th>
                        <th>Facility</th>
                    </tr>
                </thead>

                <tbody>
                    {equipment.map((item) => (
                        <tr key={item.id}>
                            <td>{item.id}</td>
                            <td>{item.serial_number}</td>
                            <td>{item.model}</td>
                            <td>{item.status}</td>
                            <td>{item.charge_level}%</td>
                            <td>{item.facility_id}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );

    const renderWorkOrders = () => (
        <>
            <h1>Work Orders</h1>

            {isAdmin && (
                <form
                    className="action-form"
                    onSubmit={createWorkOrder}
                >
                    <h3>Create Work Order</h3>

                    <label>Title</label>
                    <input
                        value={workOrderTitle}
                        onChange={(event) =>
                            setWorkOrderTitle(event.target.value)
                        }
                        required
                    />

                    <label>Priority</label>
                    <select
                        value={workOrderPriority}
                        onChange={(event) =>
                            setWorkOrderPriority(event.target.value)
                        }
                    >
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="Critical">Critical</option>
                    </select>

                    <label>Status</label>
                    <select
                        value={workOrderStatus}
                        onChange={(event) =>
                            setWorkOrderStatus(event.target.value)
                        }
                    >
                        <option value="Pending">Pending</option>
                        <option value="In-Progress">In-Progress</option>
                        <option value="Completed">Completed</option>
                        <option value="Failed">Failed</option>
                    </select>

                    <label>Equipment</label>
                    <select
                        value={workOrderEquipment}
                        onChange={(event) =>
                            setWorkOrderEquipment(event.target.value)
                        }
                        required
                    >
                        <option value="">Select equipment</option>

                        {equipment.map((item) => (
                            <option key={item.id} value={item.id}>
                                {item.serial_number} - {item.model}
                            </option>
                        ))}
                    </select>

                    <label>Technician ID</label>
                    <input
                        type="number"
                        value={workOrderTechnician}
                        onChange={(event) =>
                            setWorkOrderTechnician(event.target.value)
                        }
                        required
                    />

                    <button type="submit">
                        Create Work Order
                    </button>
                </form>
            )}

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>Equipment</th>
                        <th>Technician</th>

                        {(isAdmin || isTechnician) && (
                            <th>Actions</th>
                        )}
                    </tr>
                </thead>

                <tbody>
                    {workOrders.map((order) => (
                        <tr key={order.id}>
                            <td>{order.id}</td>
                            <td>{order.title}</td>
                            <td>{order.priority}</td>
                            <td>{order.status}</td>
                            <td>{order.equipment_id}</td>
                            <td>{order.technician_id}</td>

                            {(isAdmin || isTechnician) && (
                                <td>
                                    <select
                                        value={order.status}
                                        onChange={(event) =>
                                            updateWorkOrderStatus(
                                                order.id,
                                                event.target.value
                                            )
                                        }
                                    >
                                        <option value="Pending">Pending</option>
                                        <option value="In-Progress">
                                            In-Progress
                                        </option>
                                        <option value="Completed">
                                            Completed
                                        </option>
                                        <option value="Failed">Failed</option>
                                    </select>
                                </td>
                            )}
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );

    const renderServiceReports = () => (
        <>
            <h1>Service Reports</h1>

            {(isAdmin || isTechnician) && (
                <form
                    className="action-form"
                    onSubmit={createServiceReport}
                >
                    <h3>Create Service Report</h3>

                    <label>Work Order</label>
                    <select
                        value={reportWorkOrderId}
                        onChange={(event) =>
                            setReportWorkOrderId(event.target.value)
                        }
                        required
                    >
                        <option value="">Select work order</option>

                        {workOrders.map((order) => (
                            <option key={order.id} value={order.id}>
                                #{order.id} - {order.title}
                            </option>
                        ))}
                    </select>

                    <label>File URL</label>
                    <input
                        type="text"
                        value={reportFileUrl}
                        onChange={(event) =>
                            setReportFileUrl(event.target.value)
                        }
                        placeholder="reports/service-report.pdf"
                        required
                    />

                    <label>Notes</label>
                    <textarea
                        value={reportNotes}
                        onChange={(event) =>
                            setReportNotes(event.target.value)
                        }
                        placeholder="Service notes..."
                    />

                    <button type="submit">
                        Create Report
                    </button>
                </form>
            )}

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Work Order</th>
                        <th>File</th>
                        <th>Notes</th>
                        <th>Created</th>
                    </tr>
                </thead>

                <tbody>
                    {serviceReports.map((report) => (
                        <tr key={report.id}>
                            <td>{report.id}</td>
                            <td>{report.work_order_id}</td>
                            <td>{report.file_url}</td>
                            <td>{report.notes || "—"}</td>
                            <td>
                                {report.created_at
                                    ? new Date(report.created_at).toLocaleString()
                                    : "—"}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );

    const renderPage = () => {
        switch (activePage) {
            case "hospitals":
                return renderHospitals();

            case "equipment":
                return renderEquipment();

            case "workOrders":
                return renderWorkOrders();

            case "serviceReports":
                return renderServiceReports();

            default:
                return renderDashboard();
        }
    };

    return (
        <div className="app-layout">
            <aside className="sidebar">
                <h2>MedFlow</h2>

                {user && (
                    <div className="user-info">
                        <strong>{user.username}</strong>
                        <span>{user.role}</span>
                    </div>
                )}

                <nav>
                    <button onClick={() => setActivePage("dashboard")}>
                        Dashboard
                    </button>

                    <button onClick={() => setActivePage("hospitals")}>
                        Hospitals
                    </button>

                    <button onClick={() => setActivePage("equipment")}>
                        Equipment
                    </button>

                    <button onClick={() => setActivePage("workOrders")}>
                        Work Orders
                    </button>

                    <button onClick={() => setActivePage("serviceReports")}>
                        Service Reports
                    </button>
                </nav>

                <button className="logout-button" onClick={onLogout}>
                    Logout
                </button>
            </aside>

            <main className="main-content">
                {error && <p className="error">{error}</p>}
                {renderPage()}
            </main>
        </div>
    );
}

export default Dashboard;