
from rides.models import Rides
from .customs import WalletPayment
from .serializer import PayRidesSerializer
from notifications.models import Notifications
from notifications.custums import RetrieveBackofficeUser
from clients.models import Clients 
from drivers.models import Drivers
from drivers.models import DriverGrade as DriverGradeModel


class DriverEarningsSettlement:
    def __init__(self):
        pass
    def execute_driver_settlement(self, rides_id):
        try:
            payments_data = {}
            print("Starting driver settlement process...")

            rides_info = Rides.objects.get(id=rides_id)
            final_price = float(rides_info.final_price)

            payments_data['client_id'] = str(rides_info.client_id.id)
            payments_data['amount'] = final_price
            payments_data['payments_status'] = 'completed'
            payments_data['payments_method'] = 'orange_money'
            payments_data['phone_number'] = rides_info.client_id.phone_number

            # Get the driver's current grade
            try:
                driver_grade = DriverGradeModel.objects.filter(
                    driver_id=rides_info.driver_id,
                    is_current=True
                ).select_related('grade').first()
                
                if not driver_grade:
                    # Fallback to default commission if no grade is assigned
                    commission_rate = 15.0  # Default commission rate
                    print(f"Warning: No active grade found for driver {rides_info.driver_id.id}, using default commission rate of {commission_rate}%")
                else:
                    commission_rate = float(driver_grade.grade.commission_rate)
                
                # Update driver's wallet
                WalletPayment.retrieve_a_wallet_driver_amount(
                    final_rides=final_price,
                    driver_id=str(rides_info.driver_id.id),
                    percentage=commission_rate
                )
                
            except Exception as e:
                print(f"Error processing grade-based commission: {str(e)}")
            serializer = PayRidesSerializer(data=payments_data)
            if serializer.is_valid():
                serializer.save()
                print("Payment recorded successfully.")

            else:
                print(f"Serializer errors: {serializer.errors}")

        except Rides.DoesNotExist:
            print("Error: Ride not found.")
        except Drivers.DoesNotExist:
            print("Error: Driver not found.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
