
from pythonosc import udp_client

..................

        outWeight = np.zeros(self.numPoses_orig)
        outWeight[self.activePosesBool] = res.x

        outWeight = outWeight * (outWeight > 1.0e-9)
        # print (outWeight)
        blend=["eyeBlinkLeft", "eyeLookDownLeft", "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeSquintLeft", "eyeWideLeft", "eyeBlinkRight", "eyeLookDownRight", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeSquintRight", "eyeWideRight", "jawForward", "jawLeft", "jawRight", "jawOpen", "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight", "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight", "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper", "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthUpperUpLeft", "mouthUpperUpRight", "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight", "cheekPuff", "cheekSquintLeft", "cheekSquintRight", "noseSneerLeft", "noseSneerRight", "tongueOut"]
        client=udp_client.SimpleUDPClient('127.0.0.1',5008)
        #client=udp_client.SimpleUDPClient('47.94.83.12',5008)
        osc_array=outWeight.tolist()
        
        messagex=str(osc_array).replace("[","").replace("]","")
        print(str(messagex))
        client.send_message(str(messagex),0)

        #count=0
        #for i in osc_array:
         #   client.send_message('/'+str(blend[count]),i)
          #  count+=1
         #   print(str(blend[count]))
         #   print(i)

        return outWeight

